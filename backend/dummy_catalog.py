"""
Dummy course catalog — seed data for development and demo.

Six fictional courses with deliberate topic overlaps so the Catalog Search
agent has meaningful content to reason about:

  • Ethics appears in courses 2, 4, and partially in 1 and 5
  • ML fundamentals overlap between courses 1 and 3
  • Hands-on LLM content overlaps between courses 3 and 5
  • Healthcare regulatory content in course 4 overlaps with governance in course 2
  • Course 6 has prerequisite-level content for courses 1 and 4
"""

import json
import sqlite3

from config import DB_PATH

COURSES = [
    {
        "title": "Introduction to Machine Learning for Business Leaders",
        "duration": "full-day",
        "audience": "Executives",
        "topic_area": "ML",
        "description": (
            "A practical introduction to machine learning for business leaders. "
            "Focuses on strategic applications, build-vs-buy decisions, and measuring "
            "ROI — no coding required."
        ),
        "modules": [
            {
                "title": "ML Fundamentals",
                "description": "What machine learning is, how it works, and what problems it solves",
                "topics": [
                    "supervised learning",
                    "unsupervised learning",
                    "reinforcement learning",
                    "model training",
                    "inference",
                ],
                "duration_minutes": 90,
                "order_index": 0,
            },
            {
                "title": "Business Applications of ML",
                "description": "Real-world ML use cases across industries, with emphasis on recognizable examples",
                "topics": [
                    "predictive analytics",
                    "customer segmentation",
                    "demand forecasting",
                    "recommendation systems",
                    "fraud detection",
                ],
                "duration_minutes": 90,
                "order_index": 1,
            },
            {
                "title": "Build vs. Buy: A Decision Framework",
                "description": "How to evaluate whether to build custom ML solutions or purchase off-the-shelf",
                "topics": [
                    "make-or-buy analysis",
                    "vendor evaluation",
                    "total cost of ownership",
                    "lock-in risk",
                ],
                "duration_minutes": 60,
                "order_index": 2,
            },
            {
                "title": "Case Studies: ML Successes and Failures",
                "description": "Real-world examples of ML projects — what worked, what failed, and why",
                "topics": [
                    "retail ML",
                    "financial ML",
                    "manufacturing ML",
                    "project failure analysis",
                ],
                "duration_minutes": 60,
                "order_index": 3,
            },
            {
                "title": "ROI of ML Projects",
                "description": "How to measure, forecast, and communicate the business value of ML investments",
                "topics": [
                    "ROI calculation",
                    "KPI definition",
                    "business case development",
                    "stakeholder communication",
                ],
                "duration_minutes": 60,
                "order_index": 4,
            },
        ],
    },
    {
        "title": "Responsible AI: Ethics and Governance",
        "duration": "half-day",
        "audience": "Mixed",
        "topic_area": "Ethics",
        "description": (
            "An exploration of ethical principles, bias mitigation, and governance "
            "frameworks for responsible AI development and deployment."
        ),
        "modules": [
            {
                "title": "Bias and Fairness in AI",
                "description": "Understanding sources of bias in AI systems and practical approaches to fairness",
                "topics": [
                    "types of bias",
                    "representation bias",
                    "fairness metrics",
                    "bias mitigation techniques",
                    "demographic parity",
                ],
                "duration_minutes": 60,
                "order_index": 0,
            },
            {
                "title": "Transparency and Explainability",
                "description": "Making AI decisions understandable to stakeholders and affected users",
                "topics": [
                    "explainable AI (XAI)",
                    "model cards",
                    "LIME",
                    "SHAP",
                    "documentation standards",
                ],
                "duration_minutes": 45,
                "order_index": 1,
            },
            {
                "title": "Accountability Frameworks",
                "description": "Governance structures and processes for organizational AI accountability",
                "topics": [
                    "AI governance",
                    "roles and responsibilities",
                    "audit processes",
                    "incident response",
                ],
                "duration_minutes": 45,
                "order_index": 2,
            },
            {
                "title": "Regulatory Landscape",
                "description": "Current and emerging AI regulations across jurisdictions",
                "topics": [
                    "EU AI Act",
                    "GDPR",
                    "US AI policy",
                    "Canadian AI framework",
                    "compliance requirements",
                ],
                "duration_minutes": 45,
                "order_index": 3,
            },
            {
                "title": "Ethics Review Processes",
                "description": "Implementing ethics reviews as part of the AI development lifecycle",
                "topics": [
                    "ethics committees",
                    "review checklists",
                    "continuous monitoring",
                    "red-teaming",
                ],
                "duration_minutes": 45,
                "order_index": 4,
            },
        ],
    },
    {
        "title": "Deep Learning Fundamentals",
        "duration": "multi-day",
        "audience": "Junior Devs / Senior Engineers",
        "topic_area": "ML",
        "description": (
            "A hands-on three-day course covering the theory and practice of deep "
            "learning, from basic neural networks through transformers."
        ),
        "modules": [
            {
                "title": "Neural Networks from Scratch",
                "description": "Building and training a basic neural network to understand the fundamentals",
                "topics": [
                    "perceptrons",
                    "activation functions",
                    "forward pass",
                    "backpropagation",
                    "gradient descent",
                ],
                "duration_minutes": 180,
                "order_index": 0,
            },
            {
                "title": "Convolutional Neural Networks (CNNs)",
                "description": "Architecture and applications of CNNs for image and sequence processing",
                "topics": [
                    "convolution operations",
                    "pooling",
                    "feature maps",
                    "image classification",
                    "object detection",
                ],
                "duration_minutes": 150,
                "order_index": 1,
            },
            {
                "title": "Recurrent Neural Networks and LSTMs",
                "description": "Sequential models for time series and natural language processing",
                "topics": [
                    "RNN architecture",
                    "vanishing gradients",
                    "LSTM",
                    "GRU",
                    "sequence modeling",
                ],
                "duration_minutes": 150,
                "order_index": 2,
            },
            {
                "title": "The Transformer Architecture",
                "description": "Attention mechanisms and the transformer model that powers modern LLMs",
                "topics": [
                    "attention mechanism",
                    "self-attention",
                    "multi-head attention",
                    "positional encoding",
                    "encoder-decoder",
                ],
                "duration_minutes": 180,
                "order_index": 3,
            },
            {
                "title": "Training Pipelines and Optimization",
                "description": "Practical techniques for training deep learning models effectively",
                "topics": [
                    "optimizers",
                    "learning rate schedules",
                    "batch normalization",
                    "dropout",
                    "regularization",
                ],
                "duration_minutes": 120,
                "order_index": 4,
            },
            {
                "title": "Practical Exercises: End-to-End Model Training",
                "description": "Hands-on project: train a model from data prep through evaluation",
                "topics": [
                    "data preprocessing",
                    "model selection",
                    "hyperparameter tuning",
                    "evaluation metrics",
                    "model serving",
                ],
                "duration_minutes": 240,
                "order_index": 5,
            },
        ],
    },
    {
        "title": "AI for Healthcare Applications",
        "duration": "full-day",
        "audience": "Technical PMs / Senior Engineers",
        "topic_area": "Applied AI",
        "description": (
            "A domain-specific course on applying AI in healthcare — covering medical "
            "imaging, clinical NLP, ethics, and regulatory requirements in Canada and the US."
        ),
        "modules": [
            {
                "title": "Medical Imaging with AI",
                "description": "Using computer vision and deep learning for radiology, pathology, and diagnostics",
                "topics": [
                    "X-ray analysis",
                    "MRI segmentation",
                    "pathology slide analysis",
                    "diagnostic accuracy",
                    "FDA approval for medical AI",
                ],
                "duration_minutes": 90,
                "order_index": 0,
            },
            {
                "title": "NLP for Clinical Notes",
                "description": "Extracting structured information and insights from unstructured clinical text",
                "topics": [
                    "named entity recognition",
                    "clinical coding (ICD)",
                    "de-identification",
                    "clinical summarization",
                    "FHIR",
                ],
                "duration_minutes": 90,
                "order_index": 1,
            },
            {
                "title": "Ethics in Healthcare AI",
                "description": "Special ethical considerations when AI affects patient outcomes",
                "topics": [
                    "patient safety",
                    "algorithmic bias in healthcare",
                    "informed consent",
                    "explainability for clinicians",
                    "health equity",
                ],
                "duration_minutes": 60,
                "order_index": 2,
            },
            {
                "title": "Regulatory Requirements",
                "description": (
                    "Navigating Health Canada and FDA approval processes for "
                    "AI-enabled medical devices"
                ),
                "topics": [
                    "SaMD classification",
                    "Health Canada AI framework",
                    "FDA 510(k)",
                    "post-market surveillance",
                    "software as a medical device",
                ],
                "duration_minutes": 90,
                "order_index": 3,
            },
            {
                "title": "Case Studies in Healthcare AI",
                "description": "Real-world deployments: successes, failures, and lessons learned",
                "topics": [
                    "sepsis prediction",
                    "diabetic retinopathy screening",
                    "drug discovery",
                    "hospital readmission prediction",
                ],
                "duration_minutes": 60,
                "order_index": 4,
            },
        ],
    },
    {
        "title": "Building with Large Language Models",
        "duration": "full-day",
        "audience": "Junior Devs / Senior Engineers",
        "topic_area": "Applied AI",
        "description": (
            "A hands-on full-day course on building production-grade applications with "
            "LLMs — from prompt engineering through deployment, evaluation, and cost management."
        ),
        "modules": [
            {
                "title": "Prompt Engineering",
                "description": "Techniques for crafting effective prompts for different tasks and models",
                "topics": [
                    "zero-shot prompting",
                    "few-shot prompting",
                    "chain-of-thought",
                    "system prompts",
                    "prompt templates",
                ],
                "duration_minutes": 90,
                "order_index": 0,
            },
            {
                "title": "Retrieval-Augmented Generation (RAG)",
                "description": "Grounding LLM responses in external knowledge sources",
                "topics": [
                    "vector databases",
                    "embeddings",
                    "semantic search",
                    "chunking strategies",
                    "hybrid retrieval",
                ],
                "duration_minutes": 90,
                "order_index": 1,
            },
            {
                "title": "Fine-Tuning LLMs",
                "description": "When and how to fine-tune models for specific domains or tasks",
                "topics": [
                    "supervised fine-tuning",
                    "LoRA",
                    "PEFT",
                    "instruction tuning",
                    "dataset preparation",
                ],
                "duration_minutes": 90,
                "order_index": 2,
            },
            {
                "title": "Evaluation and Testing",
                "description": "Rigorous methods for evaluating LLM application quality",
                "topics": [
                    "LLM evaluation frameworks",
                    "RAGAS",
                    "human evaluation",
                    "automated metrics",
                    "red-teaming",
                ],
                "duration_minutes": 60,
                "order_index": 3,
            },
            {
                "title": "Deployment and Cost Management",
                "description": "Production deployment patterns and strategies for managing LLM costs",
                "topics": [
                    "model serving",
                    "caching",
                    "rate limiting",
                    "cost estimation",
                    "model routing",
                ],
                "duration_minutes": 60,
                "order_index": 4,
            },
            {
                "title": "Responsible Use of LLMs",
                "description": "Safety, fairness, and responsible deployment of LLM-powered applications",
                "topics": [
                    "hallucination mitigation",
                    "content filtering",
                    "output validation",
                    "transparency",
                    "user consent",
                ],
                "duration_minutes": 60,
                "order_index": 5,
            },
        ],
    },
    {
        "title": "Data Literacy for Non-Technical Teams",
        "duration": "1hr talk",
        "audience": "Non-technical",
        "topic_area": "Data Science",
        "description": (
            "A two-hour accessible introduction to data literacy — helping non-technical "
            "professionals read data, understand statistics, and make data-informed decisions."
        ),
        "modules": [
            {
                "title": "What Is Data?",
                "description": "Foundational concepts: what data is, how it's collected, and why it matters",
                "topics": [
                    "structured vs unstructured data",
                    "data types",
                    "data quality",
                    "data provenance",
                ],
                "duration_minutes": 20,
                "order_index": 0,
            },
            {
                "title": "Reading Charts and Visualizations",
                "description": "How to interpret common chart types and spot misleading visualizations",
                "topics": [
                    "bar charts",
                    "line charts",
                    "scatter plots",
                    "misleading axes",
                    "correlation vs causation",
                ],
                "duration_minutes": 25,
                "order_index": 1,
            },
            {
                "title": "Basic Statistics for Decision-Makers",
                "description": "The statistical concepts that matter most for non-technical professionals",
                "topics": [
                    "mean/median/mode",
                    "variance",
                    "percentiles",
                    "statistical significance",
                    "sample size",
                ],
                "duration_minutes": 25,
                "order_index": 2,
            },
            {
                "title": "Data-Driven Decision Making",
                "description": "Frameworks for incorporating data into decisions without over-relying on it",
                "topics": [
                    "decision frameworks",
                    "data vs intuition",
                    "A/B testing basics",
                    "confirmation bias",
                ],
                "duration_minutes": 20,
                "order_index": 3,
            },
            {
                "title": "Common Pitfalls and How to Avoid Them",
                "description": "The most common data mistakes non-technical people make — and how to avoid them",
                "topics": [
                    "survivorship bias",
                    "overfitting to noise",
                    "cherry-picking data",
                    "p-hacking",
                ],
                "duration_minutes": 20,
                "order_index": 4,
            },
            {
                "title": "Hands-On: Spreadsheet Exercise",
                "description": "Working with a simple dataset in spreadsheets to practice data-driven thinking",
                "topics": [
                    "pivot tables",
                    "basic formulas",
                    "chart creation",
                    "summarizing data",
                ],
                "duration_minutes": 10,
                "order_index": 5,
            },
        ],
    },
]


def seed_catalog() -> None:
    """Insert dummy courses into the database if the catalog is empty."""
    conn = sqlite3.connect(DB_PATH)

    count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    if count > 0:
        print(f"Catalog already seeded ({count} courses found). Skipping.")
        conn.close()
        return

    for course in COURSES:
        cur = conn.execute(
            """
            INSERT INTO courses (title, duration, audience, topic_area, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                course["title"],
                course["duration"],
                course["audience"],
                course["topic_area"],
                course["description"],
            ),
        )
        course_id = cur.lastrowid

        for module in course["modules"]:
            conn.execute(
                """
                INSERT INTO course_modules
                    (course_id, title, description, topics, duration_minutes, order_index)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    course_id,
                    module["title"],
                    module["description"],
                    json.dumps(module["topics"]),
                    module["duration_minutes"],
                    module["order_index"],
                ),
            )

    conn.commit()
    conn.close()
    print(f"Seeded {len(COURSES)} courses into the catalog.")


if __name__ == "__main__":
    from database import init_db_sync

    init_db_sync()
    seed_catalog()
