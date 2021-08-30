from typing import TypedDict, Optional

class CompanyType(TypedDict):
    id: str
    name: str
    link: str


class ProductType(TypedDict):
    id: str
    title: str
    link: str
    image_link: str
    availability: str
    price: str
    sale_price: str
    product_type: str
    brand: str
    identifier_exists: str
    condition: str
    adult: str
    has_price: bool
    
    
class CategoryMapItemType(TypedDict):
    name: str
    parent: Optional[str]
