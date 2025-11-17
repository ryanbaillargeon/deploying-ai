<!-- 5493bc68-8039-4c90-b7fb-50fb9ed54715 78278bf9-20c8-409d-af7d-dc71a13b8a34 -->
# Implementation Plan: Assignment 1 Improvements

## Overview

Apply Assignment 1 lessons (structured outputs, evaluation metrics, self-correction, prompt separation, distinct tones) to enhance the YouTube History Chat system.

## Implementation Steps

### Step 1: Create Pydantic Models for Structured Outputs

**File:** `05_src/assignment_chat/src/services/api_service.py`

Add Pydantic models at the top of the file:

- `VideoSummaryItem` - Individual video information
- `VideoListSummary` - Complete video list response with tone tracking
- `StatisticsSummary` - Statistics response with tone tracking
- `VideoDetailsSummary` - Video details response
- `ChannelDetailsSummary` - Channel details response

Update transformation methods (`transform_video_list`, `transform_statistics`, `transform_video_details`, `transform_channel_details`) to return Pydantic models instead of strings. Keep backward compatibility by converting to strings in tool functions.

### Step 2: Create Response Evaluator Module

**New File:** `05_src/assignment_chat/src/core/response_evaluator.py`

Implement:

- `ResponseEvaluation` Pydantic model with 4 metrics (coherence, tonality, relevance, safety) each with score (0-1) and reason
- `ResponseEvaluator` class that uses LLM with structured output to evaluate responses
- 5 assessment questions per metric (20 total questions) embedded in evaluation prompt
- `needs_enhancement` boolean based on threshold (e.g., any score < 0.7)

### Step 3: Create Response Enhancer Module

**New File:** `05_src/assignment_chat/src/core/response_enhancer.py`

Implement:

- `ResponseEnhancer` class that takes evaluation feedback and improves responses
- `enhance()` method that only enhances if `needs_enhancement` is True
- `_build_enhancement_prompt()` method that creates targeted improvement prompts based on low-scoring metrics

### Step 4: Create Separated Prompt System

**New File:** `05_src/assignment_chat/src/core/prompts.py`

Implement:

- `DEVELOPER_INSTRUCTIONS` - Static instructions for the YouTube History Curator personality
- `PERSONALITY_GUIDELINES` - Detailed personality and tone guidelines
- `SYSTEM_CONTEXT_TEMPLATE` - Dynamic template for tools, user query, and conversation history
- `get_system_prompt()` function that combines static instructions with dynamic context
- `format_conversation_history()` helper function

### Step 5: Update Chat Engine Integration

**File:** `05_src/assignment_chat/src/core/chat_engine.py`

Changes:

- Import new modules (`prompts`, `response_evaluator`, `response_enhancer`)
- Remove hardcoded `system_prompt` from `__init__`
- Initialize `ResponseEvaluator` and `ResponseEnhancer` instances
- Update `process_message()` to:
- Build dynamic system prompt using `get_system_prompt()`
- Evaluate final response before returning
- Enhance response if evaluation indicates issues
- Log evaluation and enhancement steps

### Step 6: Update API Service for Structured Outputs

**File:** `05_src/assignment_chat/src/services/api_service.py`

Changes:

- Import Pydantic models
- Modify transformation methods to return Pydantic models
- Update tool functions to convert structured outputs to natural language strings for LLM consumption
- Ensure backward compatibility with existing tool interface

## Key Implementation Details

### Pydantic Models Structure

- All summary models include `tone` field (default: "conversational" or "analytical")
- Models include both structured data and `summary_text` for natural language output
- Validation ensures required fields are present

### Evaluation Metrics

- **Coherence**: Logical structure, idea connections, flow
- **Tonality**: Personality match, conversational style, enthusiasm
- **Relevance**: Answer quality, accuracy, completeness
- **Safety**: Restricted topics avoidance, appropriateness

### Prompt Separation

- Static instructions: Core personality, principles, restrictions
- Dynamic context: Tools, current query, recent history
- Template-based assembly for maintainability

### Personality Guidelines

- Enthusiastic, analytical, conversational, supportive
- Communication patterns: Warm openings, natural statistics, celebration of discoveries
- Avoid: Robotic language, generic responses, data dumps without insights

## Testing Considerations

- Unit tests for Pydantic model validation
- Unit tests for evaluation scoring logic
- Unit tests for enhancement prompt building
- Integration tests for full pipeline (query → tool → evaluation → enhancement)
- Manual testing to verify personality consistency and quality improvements

## Files to Create/Modify

**New Files:**

- `05_src/assignment_chat/src/core/response_evaluator.py`
- `05_src/assignment_chat/src/core/response_enhancer.py`
- `05_src/assignment_chat/src/core/prompts.py`

**Modified Files:**

- `05_src/assignment_chat/src/core/chat_engine.py`
- `05_src/assignment_chat/src/services/api_service.py`

### To-dos

- [x] Add Pydantic models (VideoSummaryItem, VideoListSummary, StatisticsSummary, etc.) to api_service.py with tone tracking fields
- [x] Update transformation methods in api_service.py to return Pydantic models while maintaining backward compatibility
- [x] Create response_evaluator.py with ResponseEvaluation model and ResponseEvaluator class using LLM-based evaluation with 4 metrics
- [x] Create response_enhancer.py with ResponseEnhancer class that improves responses based on evaluation feedback
- [x] Create prompts.py with separated developer instructions, personality guidelines, and dynamic context template
- [x] Update chat_engine.py to use dynamic prompts, integrate evaluator and enhancer, and add evaluation/enhancement pipeline