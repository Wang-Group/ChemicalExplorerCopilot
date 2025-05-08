from xdl.steps import AbstractStep
from xdl.constants import VESSEL_PROP_TYPE, REAGENT_PROP_TYPE

class Add(AbstractStep):
    """Add liquid or solid reagent. Reagent identity (ie liquid or solid) is
    determined by the ``solid`` property of a reagent in the ``Reagent``
    section.

    The quantity of the reagent can be specified using either volume (liquid
    units) or amount (all accepted units e.g. 'g', 'mL', 'eq', 'mmol').

    Name: Add

    Mandatory props:
        vessel (vessel): Vessel to add reagent to.
        reagent (reagent): Reagent to add.
        volume (float): Volume of reagent to add.
        mass (float): Mass of reagent to add.
        amount (str): amount of reagent to add in moles, grams or equivalents.
            Sanitisation occurs on call of ``on_prepare_for_execution`` for this
            prop. This will change in future.
        dropwise (bool): If ``True``, use dropwise addition speed.
        time (float): Time to add reagent over.
        stir (bool): If ``True``, stir vessel while adding reagent.
        stir_speed (float): Speed in RPM at which to stir at if stir is
            ``True``.
        viscous (bool): If ``True``, adapt process to handle viscous reagent,
            e.g. use slower addition speeds.
        purpose (str): Purpose of addition. If ``None`` assume that simply a
            reagent is being added. Roles of reagents can be specified in
            ``<Reagent>`` tag. Possible values: ``"precipitate"``,
            ``"neutralize"``, ``"basify"``, ``"acidify"`` or ``"dissolve"``.
    """
    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE, 
        "reagent": REAGENT_PROP_TYPE,
        "volume": (float, str), 
        "mass": (float, str),
        "dropwise": bool,
        "speed": float,
        "time": float,
        "stir": bool,
        "stir_speed": (float, str),
        "viscous": bool,
        "purpose": str,
        "amount": str,
    }
    
    DEFAULT_PROPS = {
        "volume": None, 
        "mass": None,
        "stir": False,
        "dropwise": False,
        "speed": None,
        "viscous": False,
        "time": None,
        "stir_speed": None,
        "purpose": None,
        "amount": None,
    }

    def __init__(
        self, 
        vessel: str,
        reagent: str,
        volume: float = "default",
        mass: float = "default",
        dropwise: bool = "default",
        speed: float = "default",
        time: float = "default",
        stir: bool = "default",
        stir_speed: float = "default",
        viscous: bool = "default",
        purpose: str = "default",
        amount: str = "default",
        **kwargs) -> None:

        super().__init__(locals())

    def get_steps(self):
        pass 
    
class AdjustPH(AbstractStep):
    """Adjust the pH of a reaction mixture with a given reagent.

    Name: AdjustPH

    Mandatory Props:
        vessel (vessel): Vessel to adjust the pH of.
        reagent (reagent): Reagent to use to adjust the pH.
        pH (float): Target pH of the adjustment.
        volume_increment (float): Volume to add to adjust the pH.
        stir (bool): If `True` then stir the vessel.
        stir_time (float): Time to stir for.
        stir_speed (float): Stirring speed in RPM.
    """

    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "reagent": REAGENT_PROP_TYPE,
        "pH": (float, dict),
        "volume_increment": (float, str),
        "stir": bool,
        "stir_time": float,
        "stir_speed": (float,str),
    }

    DEFAULT_PROPS = {
        "pH": None,
        "volume_increment": "unknown",
        "stir": True,
        "stir_speed": None,
    }
    
    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        reagent: REAGENT_PROP_TYPE,
        pH: float = "default",
        volume_increment: float = "default",
        stir: bool = "default",
        stir_time: float = None,
        stir_speed: float = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 
    
    
class HeatChillToTemp(AbstractStep):
    """Heat or chill vessel to given temperature.

    Name: HeatChillToTemp

    Mandatory props:
        vessel (vessel): Vessel to heat or chill.
        temp (float): Temperature to heat or chill vessel to.
        active (bool): If True, actively heat or chill to temp. If False, allow
            vessel to warm or cool to temp.
        continue_heatchill (bool): If True, leave heating or chilling on after
            steps finishes. If False, stop heating/chilling at end of step.
        stir (bool): If True, stir while heating or chilling.
        stir_speed (float): Speed in RPM at which to stir at if stir is True.
        purpose (str): Purpose of heating/chilling. One of "reaction",
            "control-exotherm", "unstable-reagent".
    """


    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "temp": (float, str),
        "active": bool,
        "continue_heatchill": bool,
        "stir": bool,
        "stir_speed": (float, str),
        "purpose": str,
    }

    DEFAULT_PROPS = {
        "stir": True,
        "stir_speed": None,
        "active": True,
        "continue_heatchill": True,
        "purpose": None,
    }

    
    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        temp: float,
        active: bool ="default",
        continue_heatchill: bool ="default",
        stir: bool = "default",
        stir_speed: float = "default",
        purpose: str = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 

class HeatChill(AbstractStep):
    """Heat or chill vessel to given temp for given time.

    Name: HeatChill

    Mandatory props:
        vessel (vessel): Vessel to heat or chill.
        temp (float): Temperature to heat or chill vessel to.
        time (float): Time to heat or chill vessel for.
        stir (bool): If True, stir while heating or chilling.
        stir_speed (float): Speed in RPM at which to stir at if stir is
            ``True``.
        purpose (str): Purpose of heating/chilling. One of ``"reaction"``,
            ``"control-exotherm"``, ``"unstable-reagent"``.
    """

    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "time": (float, str),
        "temp": (float, str),
        "stir": bool,
        "stir_speed": (float, str),
        "purpose": str,
    }

    DEFAULT_PROPS = {
        "stir": True,
        "stir_speed": None,
        "purpose": None,
    }

    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        time: float,
        temp: float,
        stir: bool = "default",
        stir_speed: float = "default",
        purpose: str = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 
    
class Wait(AbstractStep):
    """Wait for given time.

    Args:
        time: Time to wait
    """

    PROP_TYPES = {
        "time": (float, str)
    }

    def __init__(self, time: float, **kwargs) -> None:
        super().__init__(locals())
        
    def get_steps(self):
        pass 
    
    
class Evaporate(AbstractStep):
    """Evaporate solvent.

    Name: Evaporate

    Mandatory props:
        vessel (vessel): Vessel to evaporate solvent from.
        pressure (float): Vacuum pressure to use for evaporation.
        temp (float): Temperature to heat contents of vessel to for evaporation.
        time (float): Time to evaporate for.
        stir_speed (float): Speed at which to stir mixture during
            evaporation. If using traditional rotavap, speed in RPM at
            which to rotate evaporation flask.
    """


    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "pressure": (float, str),
        "time": (float, str),
        "temp": (float, str),
        "stir_speed": (float, str)
    }

    DEFAULT_PROPS = {
        "time": None,
        "temp": None,
        "pressure": None,
        "stir_speed": None,
    }

    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        pressure: float = "default",
        time: float = "default",
        temp: float = "default",
        stir_speed: float = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 

class Transfer(AbstractStep):
    """Transfer liquid from one vessel to another.

    The quantity to transfer can be specified using either volume (liquid units)
    or amount (all accepted units e.g. 'g', 'mL', 'eq', 'mmol').

    Name: Transfer

    Mandatory props:
        from_vessel (vessel): Vessel to transfer liquid from.
        to_vessel (vessel): Vessel to transfer liquid to.
        volume (float): Volume of liquid to transfer from from_vessel to
            to_vessel.
        amount (str): amount of reagent to add in moles, grams or equivalents.
        time (float): Time over which to transfer liquid.
        viscous (bool): If ``True``, adapt process to handle viscous liquid,
            e.g. use slower move speed.
        rinsing_solvent (reagent): Solvent to rinse from_vessel with, and
            transfer rinsings to ``to_vessel``.
        rinsing_volume (float): Volume of ``rinsing_solvent`` to rinse
            ``from_vessel`` with.
        rinsing_repeats (int): Number of rinses to perform.
        solid (bool): Behaves like AddSolid if true. Default False.
    """

    PROP_TYPES = {
        "from_vessel": VESSEL_PROP_TYPE,
        "to_vessel": VESSEL_PROP_TYPE,
        "volume": (float, str),
        "amount": str,
        "time": (float, str),
        "viscous": bool,
        "rinsing_solvent": REAGENT_PROP_TYPE,
        "rinsing_volume": float,
        "rinsing_repeats": int,
        "solid": bool,
    }

    DEFAULT_PROPS = {
        "viscous": False,
        "time": None,
        "volume": None,
        "amount": None,
        "rinsing_solvent": None,
        "rinsing_volume": None,
        "rinsing_repeats": None,
        "solid": False,
    }
    
    def __init__(
        self, 
        from_vessel: VESSEL_PROP_TYPE,
        to_vessel: VESSEL_PROP_TYPE,
        volume: float = "default",
        amount: str = "default",
        time: float = "default",
        viscous: bool = "default",
        rinsing_solvent: REAGENT_PROP_TYPE = "default",
        rinsing_volume: float = "default",
        rinsing_repeats: int = "default",
        solid: bool = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 
    
class Stir(AbstractStep):
    """Stir vessel for given time.

    Name: Stir

    Mandatory props:
        vessel (vessel): Vessel to stir.
        time (float): Time to stir vessel for.
        stir_speed (float): Speed in RPM at which to stir at.
        continue_stirring (bool): If ``True``, leave stirring on at end of step.
            Otherwise stop stirring at end of step.
        purpose (str): Purpose of stirring. Can be ``None`` or ``'dissolve'``.
            If ``None``, assumed stirring is just to mix reagents.
    """


    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "time": (str, float),
        "stir_speed": (str, float),
        "purpose": str,
        "continue_stirring": bool,
    }

    DEFAULT_PROPS = {
        "stir_speed": None,
        "purpose": None,
        "continue_stirring": False,
    }
    
    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        time: float,
        stir_speed: float = "default",
        purpose: str = "default",
        continue_stirring: bool = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 
    
class StartStir(AbstractStep):
    """Start stirring vessel.

    Name: StartStir

    Mandatory props:
        vessel (vessel): Vessel to start stirring.
        stir_speed (float): Speed in RPM at which to stir at.
        purpose (str): Purpose of stirring. Can be None or 'dissolve'. If None,
            assumed stirring is just to mix reagents.
    """

    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "stir_speed": (str, float),
        "purpose": str,
    }
    DEFAULT_PROPS = {
        "stir_speed": None,
        "purpose": None,
    }
    
    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        stir_speed: float = "default",
        purpose: str = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 


class StopStir(AbstractStep):
    """Stop stirring given vessel.

    Name: StopStir

    Mandatory props:
        vessel (vessel): Vessel to stop stirring.
    """

    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
    }
    
    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 
    
class Filter(AbstractStep):
    """Filter mixture.

    Name: Filter

    Mandatory props:
        vessel (vessel): Vessel containing mixture to filter.
        filtrate_vessel (vessel): Vessel to send filtrate to. If not given,
            filtrate is sent to waste.
        stir (bool): Stir vessel while adding reagent.
        stir_speed (float): Speed in RPM at which to stir at if stir is
            ``True``.
        temp (float): Temperature to perform filtration at. Defaults to RT.
        continue_heatchill (bool): Only applies if temp is given. If ``True``
            continue temperature control after step has finished. Otherwise
            stop temperature control at end of step.
        volume (float): Volume of liquid to withdraw. If not given, volume
            should be calculated internally in the step.
    """


    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "filtrate_vessel": VESSEL_PROP_TYPE,
        "stir": bool,
        "stir_speed": (float, str),
        "temp": (float, str),
        "volume": (float,str),
        "continue_heatchill": bool,
    }

    DEFAULT_PROPS = {
        "filtrate_vessel": None,
        "stir": True,
        "stir_speed": None,
        "temp": None,
        "volume": None,
        "continue_heatchill": False,
    }

    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        filtrate_vessel: VESSEL_PROP_TYPE,
        stir: bool = "default",
        stir_speed: float = "default",
        temp: float = "default",
        volume: float = "default",
        continue_heatchill: bool = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 

class CrystallizeStep(AbstractStep):
    """Crystallize dissolved solid by ramping temperature to given temp
    over given time.

    Name: Crystallize

    Mandatory props:
        vessel (vessel): Vessel to crystallize.
        ramp_time (float): Time over which to ramp to temp.
        ramp_temp (float): Temp to ramp to over time.
    """


    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "ramp_time": (str, float),
        "ramp_temp": (str, float),
    }

    DEFAULT_PROPS = {
        "ramp_time": None,
        "ramp_temp": None,
    }
    
    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        ramp_time: float = "default",
        ramp_temp: float = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 

class Centrifugate(AbstractStep):
    """Centrifugation reaction.


    Args:
        vessel (str): Vessel containing mixture to microwave.
        time (float): Time to stir vessel at given power.
        rotation_speed (float): speed of the centrifuge
        temp (float): centrifuge temperature.
    """

    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "rotation_speed": (str, float),
        "time": (str, float),
        "temp": (str, float),
    }

    DEFAULT_PROPS = {
        "rotation_speed": None,
        "time": None,
        "temp": None,
    }

    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        rotation_speed: float = "default",
        time: float = "default",
        temp: float = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 
    
    

class WashSolid(AbstractStep):
    """Wash solid with by adding solvent and filtering.

    Name: WashSolid

    Mandatory props:
        vessel (vessel): Vessel containing solid to wash.
        solvent (reagent): Solvent to wash solid with.
        volume (float): Volume of solvent to use.
        filtrate_vessel (vessel): Vessel to send filtrate to. If ``None``,
            filtrate is sent to waste.
        temp (float): Temperature to apply to vessel during washing.
        stir (Union[bool, str]): If ``True``, start stirring before solvent is
            added and stop stirring after solvent is removed. If ``'solvent'``,
            start stirring after solvent is added and stop stirring before
            solvent is removed. If ``False``, do not stir at all.
        stir_speed (float): Speed at which to stir at.
        time (float): Time to wait for between adding solvent and removing
            solvent.
        repeats (int): Number of washes to perform.
    """


    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "solvent": REAGENT_PROP_TYPE,
        "volume": (str, float),
        "filtrate_vessel": VESSEL_PROP_TYPE,
        "temp": (str, float),
        "stir": bool,
        "stir_speed": (str, float),
        "time": (str, float),
        "repeats": int,
    }

    DEFAULT_PROPS = {
        "filtrate_vessel": None,
        "temp": None,
        "stir": True,
        "stir_speed": None,
        "time": None,
        "repeats": 1,
    }
    
    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        solvent: REAGENT_PROP_TYPE,
        volume: float,
        filtrate_vessel: VESSEL_PROP_TYPE = "default",
        temp: float = "default",
        stir: bool = "default",
        stir_speed: float = "default",
        time: float = "default",
        repeats: int = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 
    
class Dry(AbstractStep):
    """Dry solid.

    Name: Dry

    Mandatory props:
        vessel (vessel): Vessel containing solid to dry.
        time (float): Time to apply vacuum for.
        pressure (float): Vacuum pressure to use for drying.
        temp (float): Temp to heat vessel to while drying.
        continue_heatchill (bool): If True, continue heating after step has
            finished. If False, stop heating at end of step.
    """

    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "time": (str, float),
        "pressure": (str, float),
        "temp": (str, float),
        "continue_heatchill": bool,
    }

    DEFAULT_PROPS = {
        "time": None,
        "temp": None,
        "pressure": None,
        "continue_heatchill": False,
    }
    
    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        time: float = "default",
        pressure: float = "default",
        temp: float = "default",
        continue_heatchill: bool = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 
    
class Precipitate(AbstractStep):
    """Cause precipitation by optionally adding a reagent, then changing
    temperature and stirring.

    Name: Precipitate

    Mandatory props:
        vessel (vessel): Vessel to heat/chill and stir to cause precipitation.
        temp (float): Temperature to heat/chill vessel to.
        time (float): Time to stir vessel for at given temp.
        stir_speed (float): Speed in RPM at which to stir.
        reagent (str): Optional reagent to add to trigger precipitation.
        volume (float): Volume of reagent to add to trigger precipitation.
        amount (str): amount of reagent to add in moles, grams or equivalents
        to trigger precipitation.
        add_time (float): Time to add reagent over.
    """

    PROP_TYPES = {
        "vessel": VESSEL_PROP_TYPE,
        "temp": (str, float),
        "time": (str, float),
        "stir_speed": (str, float),
        "reagent": REAGENT_PROP_TYPE,
        "volume": (str, float),
        "amount": str,
        "add_time": float,
    }
    DEFAULT_PROPS = {
        "temp": None,
        "time": None,
        "stir_speed": None,
        "reagent": None,
        "volume": None,
        "amount": None,
        "add_time": None,
    }
    
    def __init__(
        self, 
        vessel: VESSEL_PROP_TYPE,
        temp: float = "default",
        time: float = "default",
        stir_speed: float = "default",
        reagent: REAGENT_PROP_TYPE = "default",
        volume: float = "default",
        amount: str = "default",
        add_time: float = "default",
        **kwargs) -> None:

        super().__init__(locals())
    
    def get_steps(self):
        pass 