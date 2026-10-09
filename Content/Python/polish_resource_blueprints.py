"""Compact the UI update graph and finish the demo's presentation."""
import unreal
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as B
ROOT='/Game/BlueprintResourcePrototype'
def log(s): unreal.log('RESOURCE_POLISH '+str(s))
def n(g,t): return B.create_node(g,t,unreal.IntPoint(0,0))
def link(a,output,b,input):
    assert unreal.BlueprintEditorLibrary.find_output_pin(a,output).try_create_connection(unreal.BlueprintEditorLibrary.find_input_pin(b,input)),(output,input)
def setter(node,pin,value):
    assert unreal.BlueprintEditorLibrary.find_input_pin(node,pin).set_pin_value(value)
def find(g,suffix,prefix=''):
    ids=[str(x) for x in B.find_node_types(g,suffix) if str(x).split('|')[-1]==suffix and (not prefix or str(x).startswith(prefix))]
    assert ids,(suffix,prefix)
    return ids[0]

with toolset_registry.tool_raising_exceptions():
    bp=unreal.load_asset(ROOT+'/WBP_ResourceWorkshop')
    g=B.get_graph(bp,'RefreshInventory')
    B.write_graph_dsl(g,'(fn RefreshInventory ())')
    entry=next(x for x in B.find_nodes(g) if isinstance(x,unreal.K2Node_FunctionEntry))
    inventory=n(g,find(g,'GetInventory','Variables|'))
    format=n(g,'Utilities|Text|FormatText')
    pairs=[('Wood','RawWood','Древесина'),('Blank','WoodBlank','Заготовки'),('WG','WoodGear','Деревянные шестерёнки'),('Ore','IronOre','Железная руда'),('Crushed','CrushedOre','Дроблёная руда'),('Coal','Charcoal','Древесный уголь'),('Iron','IronBlank','Железные заготовки'),('MG','MetalGear','Металлические шестерёнки')]
    setter(format,'Format','\n'.join(label+': {'+pin+'}' for pin,var,label in pairs))
    log('FORMAT PINS '+str([str(p.get_pin_name()) for p in unreal.BlueprintEditorLibrary.list_input_pins(format)]))
    for pin,var,label in pairs:
        getter=n(g,find(g,'Get'+var,'Class|BPResourceInventory|'))
        link(inventory,'Inventory',getter,'self'); link(getter,var,format,pin)
    text_type=next(str(x) for x in B.find_node_types(g,'SetText') if str(x).split('|')[-1] in ['SetText','SetText(RichTextBlock)'] and any(p.name=='self' and 'Rich Text Block' in p.type_id for p in B.get_node_type_pins(g,x).input_pins))
    stock=n(g,find(g,'GetInventoryText','Variables|'))
    update_stock=B.create_node(g,text_type,unreal.IntPoint(0,0),unreal.RichTextBlock.static_class())
    link(entry,'then',update_stock,'execute'); link(stock,'InventoryText',update_stock,'self'); link(format,'Result',update_stock,'InText')
    message=n(g,find(g,'GetMessageText','Variables|'))
    latest=n(g,find(g,'GetLastMessage','Class|BPResourceInventory|'))
    link(inventory,'Inventory',latest,'self')
    update_message=B.create_node(g,text_type,unreal.IntPoint(0,0),unreal.RichTextBlock.static_class())
    link(update_stock,'then',update_message,'execute'); link(message,'MessageText',update_message,'self'); link(latest,'LastMessage',update_message,'InText')
    B.arrange_nodes(B.find_nodes(g))
    binding=B.add_function_graph(bp,'BindRecipeButtons')
    B.write_graph_dsl(binding,'(fn BindRecipeButtons ())')
    tail=next(x for x in B.find_nodes(binding) if isinstance(x,unreal.K2Node_FunctionEntry))
    for name in ['SawWood','CarveWoodGear','MakeCharcoal','CrushOre','SmeltIron','ForgeMetalGear','RepairLab','UseRadio','ShowWood','ShowOre']:
        button=n(binding,find(binding,'GetBtn_'+name,'Variables|'))
        bind=n(binding,'Button|Event|BindEventtoOnClicked')
        delegate=n(binding,'EventDispatchers|CreateEvent')
        link(button,'Btn_'+name,bind,'self'); link(delegate,'OutputDelegate',bind,'Delegate')
        B.set_create_event_function(delegate,'Click_'+name)
        link(tail,'then',bind,'execute'); tail=bind
    B.arrange_nodes(B.find_nodes(binding))
    B.compile_blueprint(bp,True)
    event=B.get_graph(bp,'EventGraph')
    B.write_graph_dsl(event,'(event AddEvent|UserInterface|EventConstruct (bind inventory (Actor|GetActorOfClass :ActorClass "/Game/BlueprintResourcePrototype/BP_ResourceInventory.BP_ResourceInventory_C")) ('+find(event,'SetInventory','Variables|')+' inventory) ('+find(event,'BindRecipeButtons')+') ('+find(event,'RefreshInventory')+'))')
    B.arrange_nodes(B.find_nodes(event))
    tree=unreal.find_object(bp,'WidgetTree')
    for widget in unreal.ObjectIterator(unreal.TextBlock):
        if widget.get_outer()!=tree: continue
        if widget.get_name().startswith('Label_'):
            font=widget.get_editor_property('font'); font.set_editor_property('size',17); widget.set_font(font)
            widget.set_auto_wrap_text(True)
        if widget.get_name()=='Label_CarveWoodGear': widget.set_text('2 заготовки → деревянная шестерёнка')
        if widget.get_name()=='Label_SmeltIron': widget.set_text('2 дробл. руды + уголь → железо')
        if widget.get_name()=='ArtCaption': widget.set_text('Мастерская: обработка материалов и изготовление деталей')
    B.compile_blueprint(bp,True); unreal.EditorAssetLibrary.save_loaded_asset(bp)
    for graph in B.list_graphs(bp):
        nodes=list(B.find_nodes(graph))
        roots=[node for node in nodes if isinstance(node,(unreal.K2Node_FunctionEntry,unreal.K2Node_Event,unreal.K2Node_CustomEvent))]
        reachable=set(roots); pending=list(roots)
        while pending:
            current=pending.pop()
            for pin in unreal.BlueprintEditorLibrary.list_all_pins(current):
                for linked in pin.list_connected_pins():
                    owner=linked.get_owning_node()
                    if owner not in reachable:
                        reachable.add(owner); pending.append(owner)
        unused=[node for node in nodes if node not in reachable]
        if roots and unused: unreal.BlueprintGraphEditor.get_graph_editor(graph).remove_nodes(unused)
    B.compile_blueprint(bp,True); unreal.EditorAssetLibrary.save_loaded_asset(bp)
    log('COMPACT GRAPH '+str(len(B.find_nodes(g)))+' NODES')
    inv=unreal.load_asset(ROOT+'/BP_ResourceInventory')
    for var in B.list_variables(inv):
        B.set_variable_category(inv,str(var),'Workshop' if str(var) in ['Workshop','WorkshopOpen'] else 'Progress' if str(var)=='LabRepaired' else 'Feedback' if str(var)=='LastMessage' else 'Resources')
    B.compile_blueprint(inv,True); unreal.EditorAssetLibrary.save_loaded_asset(inv)
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    levels.load_level(ROOT+'/Lvl_ResourceWorkshop')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        if isinstance(actor,unreal.StaticMeshActor) and 'floor' in actor.get_actor_label().lower():
            scale=actor.get_actor_scale3d(); actor.set_actor_scale3d(unreal.Vector(40,40,scale.z))
            log('FLOOR '+actor.get_actor_label()+' '+str(actor.get_actor_scale3d()))
    levels.save_current_level()
    log('DONE')
