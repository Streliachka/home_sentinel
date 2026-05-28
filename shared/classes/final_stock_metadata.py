from pydantic import BaseModel, Field


class FinalStockMetadata(BaseModel):
    status: str = Field(description="Must be 'CLEANED_AND_APPROVED'")
    modifications_made: str = Field(description="None or description of edits")
    visual_data: str = Field(
        description="Original literal visual description from the visual analyst. This is the unedited, raw description of what is in the image. It should not be changed by the SEO or Legal agents, but it should be included in the final output for reference."
    )
    title: str = Field(
        description="A natural, descriptive English sentence (7-15 words). NO '+' signs, NO slashes."
    )
    keywords: list[str] = Field(
        description="List of 35-45 STRICTLY SINGLE WORDS or 2-word phrases max separated by ';'. All lowercase. Absolutely NO long sentences, NO phrases with 'and'. Example: ['cyberpunk'; 'leather corset'; 'prague'; 'winter'; 'sunset']."
    )
