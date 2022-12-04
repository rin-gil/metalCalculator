"""Provides a metal calculator"""

from math import pi
from typing import TypedDict

from django.http import QueryDict

from metal_calc.models import MetalGrade, Metals, MetalShape


class ContextData(TypedDict):
    """Describes values for fields in the calculator"""
    shape_selected: int
    metal_type_selected: int
    metal_alloy_selected: int
    error_message: bool
    width: int
    height: int
    s: int
    s2: int
    diameter: int
    quantity: int
    length: int
    weight: str


default_context_data: ContextData = {
    "shape_selected": 1,
    "metal_type_selected": 1,
    "metal_alloy_selected": 0,
    "error_message": False,
    "width": 0,
    "height": 0,
    "s": 0,
    "s2": 0,
    "diameter": 0,
    "quantity": 0,
    "length": 0,
    "weight": "0.00",
}


class ShapeDimensionsError(Exception):
    """The profile with the specified dimensions does not exist"""


def _parse_shape(shape: str | None) -> int:
    """Checks the correctness of the selected metal shape"""
    if shape in tuple(map(str, MetalShape.objects.values_list("id", flat=True))):
        return int(shape)
    return default_context_data["shape_selected"]


def _parse_metal_type(metal_type: str | None) -> int:
    """Checks the correctness of the selected metal type"""
    if metal_type in tuple(map(str, Metals.objects.values_list("id", flat=True))):
        return int(metal_type)
    return default_context_data["metal_type_selected"]


def _parse_metal_alloy(metal_alloy: str | None) -> int:
    """Checks the correctness of the selected metal alloy"""
    if metal_alloy in tuple(map(str, MetalGrade.objects.values_list("id", flat=True))):
        return int(metal_alloy)
    return default_context_data["metal_alloy_selected"]


def _parse_value(checked_value: str | None) -> int:
    """Checks if the values entered by the user are correct"""
    if not checked_value:
        return 0
    try:
        return int(checked_value)
    except (TypeError, ValueError):
        return 0


def _calculate_volume_of_beam(width: int, height: int, s: int, s2: int, length: int) -> float:
    """Calculates beam volume"""
    if width < s2 or height < (s * 2):  # Check that the dimensions are correct
        raise ShapeDimensionsError
    return (width * height - 2 * (height - 2 * s) * (width - s2) / 2) / 1000000 * length


def _calculate_volume_of_square_bar(width: int, length: int) -> float:
    """Calculates square bar volume"""
    return width ** 2 / 1000000 * length


def _calculate_volume_of_round_bar(diameter: int, length: int) -> float:
    """Calculates round bar volume"""
    return pi * diameter ** 2 / 4 / 1000000 * length


def _calculate_volume_of_sheet(width: int, height: int, s: int, quantity: int) -> float:
    """Calculates sheet volume"""
    return width * height / 1000000 * s * quantity / 1000


def _calculate_volume_of_flat_bar(width: int, s: int, length: int) -> float:
    """Calculates flat bar volume"""
    return width * length / 1000000 * s


def _calculate_volume_of_round_tube(diameter: int, s: int, length: int) -> float:
    """Calculates round tube volume"""
    if diameter < s * 2:  # Check that the dimensions are correct
        raise ShapeDimensionsError
    return pi * (diameter ** 2 - (diameter - s * 2) ** 2) / 4 / 1000000 * length


def _calculate_volume_of_tubing(width: int, height: int, s: int, length: int) -> float:
    """Calculates tubing volume"""
    if min(width, height) < s * 2:  # Check that the dimensions are correct
        raise ShapeDimensionsError
    return (width * height - (width - s * 2) * (height - s * 2)) / 1000000 * length


def _calculate_volume_of_angle(width: int, height: int, s: int, length: int) -> float:
    """Calculates angle volume"""
    if min(width, height) < s:  # Check that the dimensions are correct
        raise ShapeDimensionsError
    return (width * s + (height - s) * s) / 1000000 * length


def _calculate_volume_of_channel(width: int, height: int, s: int, length: int) -> float:
    """Calculates channel volume"""
    if width < s * 2 or height < s:  # Check that the dimensions are correct
        raise ShapeDimensionsError
    return (width * s + (height - s) * s * 2) / 1000000 * length


def _calculate_volume_of_hex_bar(diameter: int, length: int) -> float:
    """Calculates hex bar volume"""
    return 2 * (3 ** 0.5) * (diameter / 2000) ** 2 * length


def _calculate_volume_of_shape(shape_selected: int, context: ContextData) -> float:
    """Calculates the volume of metal shapes according to the data entered by user"""
    width: int = context["width"]
    height: int = context["height"]
    s: int = context["s"]
    s2: int = context["s2"]
    diameter: int = context["diameter"]
    quantity: int = context["quantity"]
    length: int = context["length"]

    if shape_selected == 1:  # Beam
        volume: float = _calculate_volume_of_beam(width=width, height=height, s=s, s2=s2, length=length)
    elif shape_selected == 2:  # Square bar
        volume = _calculate_volume_of_square_bar(width=width, length=length)
    elif shape_selected == 3:  # Round bar
        volume = _calculate_volume_of_round_bar(diameter=diameter, length=length)
    elif shape_selected == 4:  # Sheet
        volume = _calculate_volume_of_sheet(width=width, height=height, s=s, quantity=quantity)
    elif shape_selected == 5:  # Flat bar
        volume = _calculate_volume_of_flat_bar(width=width, s=s, length=length)
    elif shape_selected == 6:  # Round tube
        volume = _calculate_volume_of_round_tube(diameter=diameter, s=s, length=length)
    elif shape_selected == 7:  # Tubing
        volume = _calculate_volume_of_tubing(width=width, height=height, s=s, length=length)
    elif shape_selected == 8:  # Angle
        volume = _calculate_volume_of_angle(width=width, height=height, s=s, length=length)
    elif shape_selected == 9:  # Channel
        volume = _calculate_volume_of_channel(width=width, height=height, s=s, length=length)
    elif shape_selected == 10:  # Hex bar
        volume = _calculate_volume_of_hex_bar(diameter=diameter, length=length)
    else:
        volume = 0.0

    return volume


def _calculate_weight_of_metal(volume: float, metal_type_selected: int, metal_alloy_selected: int) -> str:
    """Calculates the weight of the metal from the data entered by the user"""
    if metal_alloy_selected == 0:
        density: int = Metals.objects.get(pk=metal_type_selected).density
    else:
        density = MetalGrade.objects.get(pk=metal_alloy_selected).density
    return f"{round(volume * density, 2):.2f}"


def get_context_data_for_calculator_fields(request: QueryDict, context: ContextData) -> ContextData:
    """Sets the values of the calculator fields based on the data entered by the user"""
    shape_selected: int = _parse_shape(shape=request.get("metal_shape"))
    metal_type_selected: int = _parse_metal_type(metal_type=request.get("metal_type"))
    metal_alloy_selected: int = _parse_metal_alloy(metal_alloy=request.get("metal_alloy"))
    context["shape_selected"] = shape_selected
    context["metal_type_selected"] = metal_type_selected
    context["metal_alloy_selected"] = metal_alloy_selected

    width: int = _parse_value(checked_value=request.get("width"))
    height: int = _parse_value(checked_value=request.get("height"))
    s: int = _parse_value(checked_value=request.get("s"))
    s2: int = _parse_value(checked_value=request.get("s2"))
    diameter: int = _parse_value(checked_value=request.get("diameter"))
    quantity: int = _parse_value(checked_value=request.get("quantity"))
    length: int = _parse_value(checked_value=request.get("length"))
    context["width"] = width
    context["height"] = height
    context["s"] = s
    context["s2"] = s2
    context["diameter"] = diameter
    context["quantity"] = quantity
    context["length"] = length

    try:  # Check the correctness of the shape dimensions
        volume: float = _calculate_volume_of_shape(shape_selected=shape_selected, context=context)
    except ShapeDimensionsError:
        context["error_message"] = True
    else:
        context["weight"] = _calculate_weight_of_metal(
            volume=volume, metal_type_selected=metal_type_selected, metal_alloy_selected=metal_alloy_selected
        )

    return context
