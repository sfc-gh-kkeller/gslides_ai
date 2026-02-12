#!/usr/bin/env python3
"""Generate a 3-slide presentation: Why Snowflake is the Best SaaS for Data & AI."""

from gslides_ai.deck_builder import DeckBuilder


def create_snowflake_deck() -> str:
    """Create a 3-slide deck on why Snowflake is the best SaaS for data and AI."""
    
    deck = DeckBuilder(
        title="Snowflake: The AI Data Cloud",
        theme="snowflake"
    )
    
    # Slide 1: Beginning - Title
    deck.add_title_slide(
        title="Why Snowflake is the\nBest SaaS for Data & AI",
        subtitle="The unified platform powering enterprise analytics and AI"
    )
    
    # Slide 2: Middle - 5 Key Points (researched 2026)
    deck.add_content_slide(
        title="5 Reasons Snowflake Leads Data & AI",
        subtitle="Trusted by thousands of enterprises worldwide",
        bullets=[
            "AI-Native Platform — Cortex AI, Arctic LLM, Document AI, and Snowpark let teams build ML/AI without deep expertise or separate infrastructure",
            "True Multi-Cloud Freedom — Runs on AWS, Azure, and GCP with no vendor lock-in; share data across clouds and accounts instantly",
            "Elastic Scale, Predictable Cost — Separates compute from storage for instant scaling; per-second billing keeps costs 30-50% lower than alternatives",
            "Data Collaboration Built In — 2,000+ datasets on Snowflake Marketplace; zero-copy sharing eliminates ETL and data movement",
            "Enterprise Governance by Default — RBAC, dynamic masking, row-level security, and end-to-end encryption satisfy the strictest compliance requirements",
        ]
    )
    
    # Slide 3: End - Closing
    deck.add_closing_slide(
        title="Your Data. Your AI.\nOne Platform.",
        contact="snowflake.com"
    )
    
    # Build and return
    presentation_id = deck.build()
    print(f"Created presentation: {deck.get_url()}")
    return presentation_id


if __name__ == "__main__":
    create_snowflake_deck()
