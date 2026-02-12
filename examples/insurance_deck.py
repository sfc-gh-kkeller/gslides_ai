#!/usr/bin/env python3
"""Generate a Snowflake for Insurance presentation with researched content."""

from gslides_ai.deck_builder import DeckBuilder


def create_insurance_deck() -> str:
    """Create a 5-slide deck on why insurance companies should use Snowflake."""
    
    deck = DeckBuilder(
        title="Snowflake for Insurance",
        theme="snowflake"
    )
    
    # Slide 1: Title
    deck.add_title_slide(
        title="Transform Your\nInsurance Business",
        subtitle="Unlock $308B+ in fraud savings with AI-powered data"
    )
    
    # Slide 2: The Challenge - Real industry pain points
    deck.add_content_slide(
        title="The Insurance Data Crisis",
        subtitle="Legacy systems are costing you millions",
        bullets=[
            "Siloed data across policy, claims & actuarial systems blocks 360° customer views",
            "Batch processing delays prevent real-time fraud detection ($80B+ lost annually)",
            "5-10% of all claims are fraudulent — most go undetected",
            "Manual underwriting can't scale for IoT data (16.7B+ connected devices)",
            "Fragmented governance creates compliance risk under IFRS 17 & state regulations",
        ]
    )
    
    # Slide 3: Why Snowflake - Platform capabilities
    deck.add_content_slide(
        title="Why Leading Insurers Choose Snowflake",
        subtitle="One platform for all your data and AI workloads",
        bullets=[
            "Unified data foundation — consolidate policy, claims & third-party data instantly",
            "Real-time streaming — move from nightly batch to instant fraud detection",
            "AI/ML at scale — deploy models as UDFs with continuous learning",
            "Snowflake Marketplace — enrich risk models with 2,000+ external data sets",
            "Enterprise security — end-to-end encryption, RBAC, and compliance built in",
        ]
    )
    
    # Slide 4: Key Use Cases with real metrics
    deck.add_two_column_slide(
        title="Proven Insurance Use Cases",
        left_title="Underwriting & Risk",
        left_bullets=[
            "70% data self-service rate achieved",
            "Real-time IoT pricing optimization",
            "Concentration risk analysis at point of quote",
            "Third-party data enrichment via Marketplace",
        ],
        right_title="Claims & Fraud",
        right_bullets=[
            "90% faster claims processing with AI",
            "95%+ fraud detection accuracy",
            "200-1000% ROI on fraud systems",
            "50% reduction in BI dashboard time",
        ],
    )
    
    # Slide 5: Closing with CTA
    deck.add_closing_slide(
        title="Ready to Modernize?",
        contact="snowflake.com/insurance"
    )
    
    # Build and return
    presentation_id = deck.build()
    print(f"Created presentation: {deck.get_url()}")
    return presentation_id


if __name__ == "__main__":
    create_insurance_deck()
