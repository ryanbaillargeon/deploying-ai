# YouTube History AI Chat System - Project Charter

## Executive Summary

This project implements a conversational AI system that helps users explore and analyze their YouTube watch history through natural language interactions. The system integrates three distinct services: API-based data retrieval with natural language transformation, semantic search over video content, and advanced function calling for complex analytical queries.

## Project Goals

### Primary Objectives
1. **Service 1 (API Calls)**: Retrieve YouTube history data via REST API and transform structured responses into natural, conversational summaries
2. **Service 2 (Semantic Query)**: Enable semantic search over video history to find content by meaning, topics, opinions, and technologies
3. **Service 3 (Function Calling)**: Execute complex multi-parameter queries that combine semantic search with metadata analysis

### Success Criteria
- All three services operational and integrated
- Natural language interface that feels conversational
- Semantic search returns relevant results (>80% relevance)
- Complex queries execute correctly (e.g., "channels that post most about AI")
- Guardrails prevent system prompt access and block restricted topics
- Response time < 3 seconds for typical queries
- All assignment requirements met

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────┐
│                   Gradio Chat Interface                 │
│              (Conversational UI with Memory)             │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────▼────────┐    ┌────────▼────────┐
│   Chat Engine   │    │  Guardrails      │
│  (LLM + Tools)  │    │  (Input/Output)  │
└────────┬────────┘    └──────────────────┘
         │
    ┌────┴────┬──────────────┬──────────────┐
    │         │              │               │
┌───▼───┐ ┌──▼──────┐  ┌────▼──────┐  ┌────▼──────┐
│ API   │ │Semantic │  │ Function  │  │  Memory   │
│Service│ │ Service │  │  Service  │  │  Manager  │
└───┬───┘ └───┬─────┘  └─────┬──────┘  └───────────┘
    │         │              │
    │    ┌────▼─────┐        │
    │    │ ChromaDB │        │
    │    │ (Vector) │        │
    │    └──────────┘        │
    │                        │
┌───▼────────────────────────▼───┐
│   YouTube History API           │
│   (REST API - localhost:8000)  │
└─────────────────────────────────┘
```

### Technology Stack
- **LLM**: OpenAI API (GPT-4 or GPT-4o)
- **Interface**: Gradio ChatInterface
- **Vector Database**: ChromaDB with file persistence
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **API Client**: Python requests library
- **Language**: Python 3.12+

## Core Capabilities

### Service 1: API Calls with Transformation
- Retrieve video lists, statistics, channel information, and individual video details
- Transform structured JSON responses into natural language summaries
- Support pagination and filtering
- Handle errors gracefully with user-friendly messages

### Service 2: Semantic Query
- Search videos by meaning, not just keywords
- Support topic-based queries: "videos about machine learning"
- Support opinion-based queries: "videos discussing AI ethics"
- Support technology-based queries: "tutorials on React"
- Hybrid search combining semantic similarity with metadata filters (dates, channels, duration)

### Service 3: Function Calling
- Multi-parameter queries: "channels that post most about AI"
- Metadata queries: "most watched videos last month"
- Complex aggregations: Combine semantic search with statistical analysis
- Query routing: Intelligently determine which functions to call

## User Experience

### Chat Personality
The assistant will have a distinct personality as a **YouTube History Curator**:
- **Role**: Analytical assistant specializing in video history insights
- **Tone**: Helpful, analytical, conversational, and insightful
- **Capabilities**: Emphasize ability to find patterns, provide insights, and make recommendations

### Conversation Flow
1. User asks natural language question
2. System determines appropriate service(s) to use
3. Service(s) execute and return results
4. LLM synthesizes results into natural response
5. Conversation history maintained for context

### Example Interactions
- "What videos did I watch about Python last month?"
- "Which channels post the most about AI?"
- "Find me tutorials I watched on machine learning"
- "What were my most watched videos in November?"

## Project Structure

```
05_src/assignment_chat/
├── docs/                          # Project documentation
│   ├── project_charter.md        # This document
│   ├── phase_0_infrastructure.md
│   ├── phase_1_service_api.md
│   ├── phase_2_service_semantic.md
│   ├── phase_3_service_functions.md
│   └── phase_4_polish.md
├── src/                          # Source code
│   ├── services/
│   │   ├── __init__.py
│   │   ├── api_service.py        # Service 1
│   │   ├── semantic_service.py   # Service 2
│   │   └── function_service.py   # Service 3
│   ├── core/
│   │   ├── __init__.py
│   │   ├── chat_engine.py        # Main chat logic
│   │   ├── guardrails.py         # Input/output filtering
│   │   ├── memory_manager.py    # Conversation memory
│   │   └── prompts.py           # System prompts
│   ├── data/
│   │   ├── embeddings/          # Embedding generation scripts
│   │   └── chroma_db/           # ChromaDB persistent storage
│   └── utils/
│       ├── __init__.py
│       └── api_client.py        # YouTube History API client
├── tests/                        # Test files
├── app.py                       # Gradio application entry point
├── README.md                    # Project documentation
└── API_REFERENCE.md             # API documentation (existing)
```

## Assignment Requirements Compliance

### Required Services ✓
- [x] Service 1: API Calls with transformation
- [x] Service 2: Semantic Query with ChromaDB
- [x] Service 3: Function Calling for complex queries

### User Interface ✓
- [x] Chat-based interface (Gradio)
- [x] Distinct personality
- [x] Conversation memory
- [ ] Optional: Memory management for long conversations

### Guardrails ✓
- [x] Prevent system prompt access
- [x] Prevent system prompt modification
- [x] Block restricted topics (cats, dogs, horoscopes, Taylor Swift)

### Implementation ✓
- [x] Code in `./05_src/assignment_chat`
- [x] README.md with explanations
- [x] Use standard course setup (no additional libraries)

## Development Phases

1. **Phase 0**: Project Infrastructure / Data Preparation
2. **Phase 1**: Service 1 - API Calls Integration
3. **Phase 2**: Service 2 - Semantic Query Service
4. **Phase 3**: Service 3 - Function Calling Service
5. **Phase 4**: Final Integration & Polish

Each phase includes:
- Requirements validation
- Implementation
- Testing
- Documentation
- Evaluation against assignment requirements

## Future Capabilities (Outlined)

### Potential Enhancements
1. **Transcript-Based Search**: Include video transcripts in embeddings
2. **Recommendation Engine**: Suggest similar videos based on patterns
3. **Trend Analysis**: Visualize viewing trends over time
4. **Collection Management**: Create/manage collections via chat
5. **Multi-Modal Search**: Combine multiple search dimensions
6. **Query Expansion**: Auto-expand queries with synonyms
7. **Caching Layer**: Cache frequent queries
8. **Web Search Integration**: Find related external content
9. **MCP Server**: Custom MCP server for YouTube operations
10. **Advanced Analytics**: Statistical analysis of patterns

## Success Metrics

### Technical Metrics
- Response time < 3 seconds (typical queries)
- Test coverage > 80%
- Zero critical bugs
- All services operational

### Functional Metrics
- Semantic search relevance > 80%
- API transformations are natural and readable
- Function calling handles complex queries correctly
- Guardrails block all restricted content

### Assignment Compliance
- All requirements met
- Code well-documented
- README explains all decisions
- Project structure follows specifications

## Risk Management

### Technical Risks
- **API Availability**: YouTube History API may be unavailable
  - *Mitigation*: Implement retry logic and graceful degradation
- **Embedding Size**: May exceed 40MB limit
  - *Mitigation*: Monitor size, optimize storage, use compression if needed
- **Response Time**: Complex queries may be slow
  - *Mitigation*: Implement caching, optimize queries, set timeouts

### Implementation Risks
- **Scope Creep**: Project may become too expansive
  - *Mitigation*: Focus on core requirements first, add enhancements later
- **Integration Complexity**: Services may not integrate smoothly
  - *Mitigation*: Test integration early, use clear interfaces

## Timeline

The project will be developed phase-by-phase, with validation and verification at the start of each phase. Each phase should be completed before moving to the next, ensuring a solid foundation for subsequent work.

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Status**: Planning Phase

