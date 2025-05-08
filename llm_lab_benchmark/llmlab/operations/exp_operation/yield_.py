from llmlab.operations.exp_operation.basic_step import BasicStep
from llmlab.utlis.property import Property
from llmlab.operations.exp_operation.attribute_value import parse_property

class Yield(BasicStep):
    """
    The final product yield from the experiment.

    Args:
        product_name: str, mandatory
            The name of the final product yielded by the experiment.
        
        product_quantity: Union[Dict[str, Any], str, None], optional
            Represents the quantity (e.g., volume or mass) of the final product yield, which can be in one of the following formats. If not mentioned exactly, default to null.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 50.0, "unit": "mL"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 40.0, "unit": "g"}, "max": {"quantity": 60.0, "unit": "g"}}
            3. **Descriptive string**: A string describing the quantity qualitatively (e.g., "small amount", "large amount").
        
        yield_percentage: Union[Dict[str, Any], str, None], optional
            Represents the percentage yield of the final product, which can be in one of the following formats. If not mentioned exactly, default to null.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 85.0, "unit": "%"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 80.0, "unit": "%"}, "max": {"quantity": 90.0, "unit": "%"}}
            3. **Descriptive string**: A string describing the yield qualitatively (e.g., "high yield", "low yield").
    """

    def __init__(self,
                 product_name: str,
                 product_quantity: dict = None,
                 yield_percentage: dict = None):
        
        super().__init__()
        
        self.product_name = str(product_name) if product_name is not None else None
        self.product_quantity = parse_property(product_quantity) if product_quantity is not None else Property(quantity=None, unit=None)
        self.yield_percentage = parse_property(yield_percentage) if yield_percentage is not None else Property(quantity=None, unit=None)
    
    def check_ambiguity(self, mode="plain_txt"):
        pass 