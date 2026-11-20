#!/usr/bin/env python3
import typing, copy


def copy_parent(child_in: typing.Any, parent_in: typing.Any) -> None:
    if isinstance(child_in, type(parent_in)):
        if hasattr(parent_in, "__dict__"):
            # This is a big hack but I cant get the info items copied
            # to by class otherwise.
            for attr, value in parent_in.__dict__.items():
                if hasattr(child_in, attr):
                    try:
                        setattr(child_in, attr, copy.deepcopy(value))
                        continue
                    except AttributeError as _:
                        #continue
                        print(f"Failed Set Attribute: "
                              f"{child_in.__class__.__name__}.{k} = {v}")

        elif hasattr(parent_in, "__slots__"):
            # This is a big hack but I cant get the info items copied
            # to by class otherwise.
            for attr in parent_in.__slots__.keys():
                if hasattr(child_in, attr):
                    try:
                        try:
                            setattr(child_in, attr, copy.deepcopy(
                                getattr(parent_in, attr)))
                        except AttributeError as _:
                            setattr(child_in, attr, copy.deepcopy(
                                getattr(parent_in, attr)))
                            continue
                    except AttributeError as _:
                        #continue
                        print(f"Failed Set Attribute: "
                              f"{child_in.__class__.__name__}.{k}")

        else:
            print(f"Failed Set Copy Attributes: "
                  f"{parent_in.__class__.__name__} -> "
                  f"{child_in.__class__.__name__}")
    else:
        print(f"'child_in' must be a child of 'parent_in': "
              f"{child.__class__.__name__} is not a "
              f"{parent_in.__class__.__name__}")