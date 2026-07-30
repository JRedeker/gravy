"""Concrete in-process Gradio Blocks runtime for Gravy review surfaces.

The runtime pins Gradio to the 6.x release line, launches each review page with
`prevent_thread_lock=True` on a bounded port, configures bounded queue/thread
settings, and binds every surface to the existing durable decision controllers.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import gradio as gr

from .artifacts import ArtifactStore
from .schemas import (
    ChecklistRequest,
    FormField,
    FormRequest,
    GalleryRequest,
    PairwiseRequest,
    ReviewRequest,
)
from .surfaces.checklist import ChecklistSurface
from .surfaces.common import SurfaceValidationError
from .surfaces.form import FormSurface
from .surfaces.gallery import GallerySurface
from .surfaces.pairwise import PairwiseSurface

GRADIO_QUEUE_MAX_SIZE = 20
GRADIO_MAX_THREADS = 8


def _field_name(field: str | FormField) -> str:
    return field if isinstance(field, str) else field.name


def _surface_for_request(
    review_id: str, request: ReviewRequest, artifacts: ArtifactStore
):
    """Instantiate the closed surface controller for a parsed request."""
    if isinstance(request, GalleryRequest):
        return GallerySurface(review_id, request.items, artifacts)
    if isinstance(request, PairwiseRequest):
        return PairwiseSurface(review_id, request.items, artifacts)
    if isinstance(request, FormRequest):
        return FormSurface(
            review_id, tuple(_field_name(f) for f in request.fields), artifacts
        )
    if isinstance(request, ChecklistRequest):
        return ChecklistSurface(review_id, request.criteria, artifacts)
    raise ValueError(f"unsupported review request: {type(request).__name__}")


class ReviewPageController:
    """Translate UI actions into durable surface decisions.

    Kept separate from the Blocks renderer so the same logic can be exercised
    with or without starting a real Gradio listener.
    """

    def __init__(
        self, review_id: str, request: ReviewRequest, artifacts: ArtifactStore
    ) -> None:
        self.review_id = review_id
        self.surface_name = request.surface
        self._surface = _surface_for_request(review_id, request, artifacts)

    def gallery_submit(
        self, selection: str, ranking: list[str], notes: str
    ) -> dict[str, Any]:
        progress = self._surface.submit(
            selection=selection, ranking=tuple(ranking), notes=notes
        )
        return {"complete": progress.complete, "remaining": progress.remaining}

    def pairwise_choose(self, choice: str) -> dict[str, Any]:
        progress = self._surface.choose(choice)  # type: ignore[arg-type]
        pair = self._surface.current_pair
        return {
            "complete": progress.complete,
            "remaining": progress.remaining,
            "pair": pair,
        }

    def form_submit(self, values: Mapping[str, Any]) -> dict[str, Any]:
        progress = self._surface.submit(values)
        return {"complete": progress.complete, "remaining": progress.remaining}

    def checklist_submit(
        self, criterion: str, passed: bool, comment: str
    ) -> dict[str, Any]:
        progress = self._surface.submit(criterion, passed=passed, comment=comment)
        return {"complete": progress.complete, "remaining": progress.remaining}

    def _handle(self, fn, *args, **kwargs) -> dict[str, Any]:
        try:
            return fn(*args, **kwargs)
        except SurfaceValidationError as exc:
            return {"error": str(exc)}


def _build_gallery(
    controller: ReviewPageController, request: GalleryRequest
) -> gr.Blocks:
    with gr.Blocks(title="Gravy Gallery Review") as blocks:
        gr.Markdown("### Gallery review")
        for item in request.items:
            path = Path(item)
            if path.is_file():
                gr.Image(value=str(path), label=item, interactive=False)
            else:
                gr.Markdown(f"- {item}")

        selection = gr.Radio(choices=list(request.items), label="Selection")
        ranking = gr.Dropdown(
            choices=list(request.items),
            label="Ranking (select in order)",
            multiselect=True,
        )
        notes = gr.Textbox(label="Notes")
        status = gr.Textbox(label="Status", interactive=False)

        def submit(selection, ranking, notes):
            return controller._handle(
                controller.gallery_submit, selection, ranking, notes
            )

        gr.Button("Submit").click(
            submit, inputs=[selection, ranking, notes], outputs=[status]
        )
    return blocks


def _build_pairwise(
    controller: ReviewPageController, request: PairwiseRequest
) -> gr.Blocks:
    with gr.Blocks(title="Gravy Pairwise Review") as blocks:
        gr.Markdown("### Pairwise review")
        pair_md = gr.Markdown()

        def refresh() -> str:
            pair = controller._surface.current_pair
            if pair is None:
                return "**All comparisons complete.**"
            return f"**Compare:** {pair[0]} vs {pair[1]}"

        pair_md.value = refresh()

        def choose(choice: str) -> str:
            result = controller._handle(controller.pairwise_choose, choice)
            if "error" in result:
                return f"Error: {result['error']}"
            return refresh()

        with gr.Row():
            gr.Button("Left").click(lambda: choose("left"), outputs=[pair_md])
            gr.Button("Right").click(lambda: choose("right"), outputs=[pair_md])
            gr.Button("Tie").click(lambda: choose("tie"), outputs=[pair_md])
            gr.Button("Skip").click(lambda: choose("skip"), outputs=[pair_md])
    return blocks


def _build_form(controller: ReviewPageController, request: FormRequest) -> gr.Blocks:
    fields: list[FormField] = [
        FormField(name=f) if isinstance(f, str) else f for f in request.fields
    ]
    components: list[gr.components.Component] = []
    component_names: list[str] = []

    with gr.Blocks(title="Gravy Form Review") as blocks:
        gr.Markdown("### Form review")
        for field in fields:
            label = field.label if field.label is not None else field.name
            if field.type == "text":
                comp = gr.Textbox(label=label)
            elif field.type == "free_text":
                comp = gr.Textbox(label=label, lines=4)
            elif field.type == "toggle":
                comp = gr.Checkbox(label=label)
            elif field.type == "option":
                comp = gr.Radio(choices=list(field.options), label=label)
            elif field.type == "image":
                comp = gr.Image(label=label, type="filepath")
            else:
                comp = gr.Textbox(label=label)
            components.append(comp)
            component_names.append(field.name)

        status = gr.Textbox(label="Status", interactive=False)

        def submit(*values):
            return controller._handle(
                controller.form_submit,
                {name: value for name, value in zip(component_names, values)},
            )

        gr.Button("Submit").click(submit, inputs=components, outputs=[status])
    return blocks


def _build_checklist(
    controller: ReviewPageController, request: ChecklistRequest
) -> gr.Blocks:
    with gr.Blocks(title="Gravy Checklist Review") as blocks:
        gr.Markdown("### Checklist review")
        criterion = gr.Dropdown(choices=list(request.criteria), label="Criterion")
        passed = gr.Checkbox(label="Pass")
        comment = gr.Textbox(label="Comment")
        status = gr.Textbox(label="Status", interactive=False)

        def submit(criterion, passed, comment):
            return controller._handle(
                controller.checklist_submit, criterion, passed, comment
            )

        gr.Button("Submit").click(
            submit, inputs=[criterion, passed, comment], outputs=[status]
        )
    return blocks


_BUILDERS = {
    GalleryRequest: _build_gallery,
    PairwiseRequest: _build_pairwise,
    FormRequest: _build_form,
    ChecklistRequest: _build_checklist,
}


class GradioBlocksPage:
    """In-process Gradio Blocks listener backed by the durable surface controllers."""

    def __init__(
        self, review_id: str, request: ReviewRequest, artifacts: ArtifactStore
    ) -> None:
        self.review_id = review_id
        self._request = request
        self._artifacts = artifacts
        self._controller = ReviewPageController(review_id, request, artifacts)
        self._blocks: gr.Blocks | None = None

    @classmethod
    def build_for(
        cls, review_id: str, request: ReviewRequest, artifacts: ArtifactStore
    ) -> "GradioBlocksPage":
        return cls(review_id, request, artifacts)

    def launch(self, port: int) -> None:
        """Start a bounded, non-blocking Gradio listener on the given port."""
        builder = _BUILDERS[type(self._request)]
        blocks = builder(self._controller, self._request)
        blocks.queue(
            max_size=GRADIO_QUEUE_MAX_SIZE,
            default_concurrency_limit=GRADIO_MAX_THREADS,
        )
        blocks.launch(
            server_name="127.0.0.1",
            server_port=port,
            prevent_thread_lock=True,
            max_threads=GRADIO_MAX_THREADS,
            quiet=True,
            show_error=False,
            enable_monitoring=False,
            inbrowser=False,
            share=False,
            ssr_mode=False,
        )
        self._blocks = blocks

    def close(self) -> None:
        """Stop the listener and release its launch thread."""
        if self._blocks is not None:
            self._blocks.close()
            self._blocks = None
