import unreal


ASSETS = [
    "/Game/Widgets/BP_Workshop",
    "/Game/Widgets/BP_Machine_engine",
    "/Game/Widgets/T_Widget1",
    "/Game/Widgets/T_Widget2",
]


for asset_path in ASSETS:
    asset = unreal.load_asset(asset_path)
    if not asset:
        unreal.log_warning(f"BP_INSPECT missing: {asset_path}")
        continue

    unreal.log(f"BP_INSPECT asset={asset_path} class={asset.get_class().get_name()}")
    if isinstance(asset, unreal.Blueprint):
        parent = unreal.BlueprintEditorLibrary.get_blueprint_parent_class(asset)
        parent_name = parent.get_name() if parent else "None"
        graphs = [str(name) for name in unreal.BlueprintEditorLibrary.list_graph_names(asset)]
        variables = [str(name) for name in unreal.BlueprintEditorLibrary.list_member_variable_names(asset, False)]
        unreal.log(f"BP_INSPECT blueprint parent={parent_name} graphs={graphs} variables={variables}")

unreal.log("BP_INSPECT done")
