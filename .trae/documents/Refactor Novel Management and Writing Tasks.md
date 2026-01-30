# Refactor Novel Management Page and Crew Tasks

## 1. Refactor `crew_tasks.py`
### Update `outline_expansion_task`
- **Objective**: Enhance the prompt to meet specific user requirements.
- **Changes**:
    - Add explicit requirements for:
        - **Chapter Division** (章节划分)
        - **Word Count Guidance** (字数指导)
        - **Hooks/Plot Points** (爆点/钩子)
        - **Plotlines**: Main line (主线), Side line (副线), Hidden line (暗线) design and progression.
    - Ensure "Proposal" (企划书) and "Previous Outline" (上一节大纲) are clearly referenced in the context.

### Update `full_story_writing_task`
- **Objective**: Ensure Proposal, Outline, and Target Chapter are correctly prioritized.
- **Changes**:
    - Reinforce instructions to strictly follow the provided `context_outline` and `plan_content`.
    - Strengthen output format requirements for easier parsing (standard Markdown headers).

## 2. Refactor `services/writing_service.py`
### Update `continue_writing_chapters`
- **Objective**: Allow manual control over start chapter and outline content.
- **Signature Change**: Add `start_chapter: int = None` and `manual_outline: str = None`.
- **Logic**:
    - If `start_chapter` is provided, use it. Otherwise, auto-detect.
    - If `manual_outline` is provided, use it directly. Otherwise, query DB for `outline_segments`.
    - Ensure `plan_content` (Proposal) is retrieved and passed to the task.

## 3. Refactor `services/novel_service.py`
### Expose Outline Management Methods
- **Objective**: Allow UI to update outline segments.
- **Changes**:
    - Add `update_outline_segment(segment_id, title, summary, segment_order)` method (wrapping `OutlineManager.update_outline_segment`).

## 4. Refactor `pages/3_📚_小说管理.py`
### Tab 1: Chapter Management (Smart Continuation)
- **UI Changes**:
    - Add `number_input` for **Start Chapter Number** (default to `max_chapter + 1`).
    - Add a **Selectbox/Textarea** to choose or preview/edit the **Outline** to be used.
        - Load existing outline segments that cover the target range.
        - Allow user to modify the outline text before sending to the writer.
    - Button "Start Writing" calls `writing_service.continue_writing_chapters` with specific params.

### Tab 2: Outline Management
- **UI Changes**:
    - **Generation Section**:
        - Ensure "Specify Range" mode is prominent.
        - (Backend logic in `writing_service` already handles the range, just ensuring the improved prompt is used).
    - **Existing Outlines Section**:
        - Display segments in a list.
        - For each segment:
            - **Order**: `number_input` for `segment_order`.
            - **Content**: `text_area` for `summary` (editable).
            - **Actions**:
                - "Save" button: Updates DB via `novel_service`.
                - "Delete" button: Existing functionality.

## 5. Verification
- **Test**: Generate a new outline segment with the new prompt -> Check for plotlines/hooks.
- **Test**: Edit an outline segment and save -> Check persistence.
- **Test**: Smart Continue from a specific chapter with a specific outline -> Check generated content matches requirements.
