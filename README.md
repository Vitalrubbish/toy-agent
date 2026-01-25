# PPT-Agent: AI-Powered Slide Generator

This project implements an AI agent system capable of generating high-quality presentations using the Proposer-Reviewer (Editor-Critic) paradigm. It utilizes **Slidev** as the rendering engine and **Vision LLMs** for visual quality assessment.

## Prerequisites

*   Python 3.10+
*   Node.js 18+
*   OpenAI API Key

## Setup

1.  Current directory:
    ```bash
    cd "mnt/d/forum/第一期AI Agent/PPT-agent"
    ```

2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Install Node.js dependencies:
    ```bash
    npm install
    # or
    yarn
    ```

4.  Set up environment variables:
    Create a `.env` file in the root directory:
    ```
    OPENAI_API_KEY=sk-your-api-key-here
    ```

## Usage

1.  Prepare your input text in `data/paper_summary.txt`.
2.  Run the main script:
    ```bash
    python -m src.main
    ```

## Structure

*   `src/agents`: Editor and Critic agent implementations.
*   `src/utils`: Utilities for LLM communication and Slidev execution.
*   `output`: Generated slides and history.
