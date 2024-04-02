import os
import yaml


def get_modules(folder) -> dict:
    """ """

    modules = {}

    for module in os.listdir(folder):

        if os.path.isdir(os.path.join(folder, module)) and os.path.isfile(
            os.path.join(folder, module, "STARK.module")
        ):
            module_config_file = os.path.join(folder, module, "STARK.module")
            with open(module_config_file) as f:
                module_config = yaml.safe_load(f)

            modules[module] = module_config

            modules[module]["submodules"] = {}

            for submodule in os.listdir(os.path.join(folder, module)):

                if os.path.isdir(
                    os.path.join(folder, module, submodule)
                ) and os.path.isfile(
                    os.path.join(folder, module, submodule, "STARK.module")
                ):
                    submodule_config_file = os.path.join(
                        folder, module, submodule, "STARK.module"
                    )
                    try:
                        with open(submodule_config_file) as f:
                            submodule_config = yaml.safe_load(f)

                            for submodule_config_entry in submodule_config.get(
                                "submodules", {}
                            ):
                                modules[module]["submodules"][
                                    submodule_config_entry
                                ] = submodule_config.get("submodules", {}).get(
                                    submodule_config_entry, {}
                                )
                    except:
                        print(f"warning: Module '{module}/{submodule}' not loaded")

    return modules
