"""Assemble pickup actors, input, and an isolated playable Blueprint demo map."""
import unreal, json
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as B
ROOT='/Game/BlueprintResourcePrototype'
def log(x): unreal.log('RESOURCE_WORLD '+str(x))
def q(x): return json.dumps(x,ensure_ascii=False)
def find(g,suffix):
    names=[str(n) for n in B.find_node_types(g,suffix) if str(n).split('|')[-1].lower()==suffix.lower()]
    assert names,(g.get_name(),suffix)
    return next((n for n in names if n.startswith('Variables|') or n.startswith('Default|')),names[0])
def get(g,v): return '('+find(g,'Get'+v)+')'
def setv(g,v,expr): return '('+find(g,'Set'+v)+' '+expr+')'
def fn(bp,name,body):
    g=B.add_function_graph(bp,name)
    B.write_graph_dsl(g,'(fn '+name+' () '+body(g)+')')
    B.arrange_nodes(B.find_nodes(g)); log('FUNCTION '+name)
def save(bp):
    B.compile_blueprint(bp,True); assert unreal.EditorAssetLibrary.save_loaded_asset(bp)
def newbp(name,parent):
    return unreal.load_asset(ROOT+'/'+name) or B.create(ROOT,name,parent)
def addvar(bp,name,type_name):
    if name not in [str(v) for v in B.list_variables(bp)]: B.add_variable(bp,name,type_name)
def addref(bp,name,cls):
    if name not in [str(v) for v in B.list_variables(bp)]: B.add_object_variable(bp,name,cls)
def connect(a,out,b,inp):
    assert unreal.BlueprintEditorLibrary.find_output_pin(a,out).try_create_connection(unreal.BlueprintEditorLibrary.find_input_pin(b,inp))

with toolset_registry.tool_raising_exceptions():
    inv=unreal.load_asset(ROOT+'/BP_ResourceInventory')
    screen=unreal.load_asset(ROOT+'/WBP_ResourceWorkshop'); assert screen
    pickup=newbp('BP_ResourcePickup',unreal.StaticMeshActor.static_class())
    addvar(pickup,'IsOre','bool'); addvar(pickup,'Collected','bool')
    B.compile_blueprint(pickup)
    def collect(g):
        return '(if (not '+get(g,'Collected')+') '+setv(g,'Collected','true')+' (bind inventory (Actor|GetActorOfClass :ActorClass '+q(inv.generated_class().get_path_name())+')) (if '+get(g,'IsOre')+' ('+find(g,'CollectOre')+' :self inventory) (else ('+find(g,'CollectWood')+' :self inventory))) (Actor|DestroyActor :self self))'
    fn(pickup,'Collect',collect)
    save(pickup)
    wood=newbp('BP_WoodPickup',pickup.generated_class())
    ore=newbp('BP_IronOrePickup',pickup.generated_class())
    for bp,mesh,is_ore in [(wood,'Cylinder',False),(ore,'Sphere',True)]:
        B.compile_blueprint(bp)
        cdo=unreal.get_default_object(bp.generated_class())
        cdo.set_editor_property('IsOre',is_ore)
        comp=cdo.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/'+mesh))
        comp.set_collision_profile_name('OverlapAllDynamic')
        save(bp)
    addref(inv,'Workshop',screen.generated_class()); addvar(inv,'WorkshopOpen','bool')
    B.compile_blueprint(inv)
    fn(inv,'OpenWorkshop',lambda g:
       '(if (not '+get(g,'WorkshopOpen')+') (bind pc (Game|GetPlayerController)) '
       '(bind ui (UserInterface|CreateWidget :Class '+q(screen.generated_class().get_path_name())+' :OwningPlayer pc)) '+setv(g,'Workshop','ui')+
       '(UserInterface|Viewport|AddtoViewport :self ui) (Class|PlayerController|SetShowMouseCursor :bShowMouseCursor true :self pc) '
       '(Input|SetInputModeGameAndUI :PlayerController pc :bHideCursorDuringCapture false) '+setv(g,'WorkshopOpen','true')+')')
    fn(inv,'CloseWorkshop',lambda g:
       '(if '+get(g,'WorkshopOpen')+' (Widget|RemovefromParent :self '+get(g,'Workshop')+') '
       '(bind pc (Game|GetPlayerController)) (Class|PlayerController|SetShowMouseCursor :bShowMouseCursor false :self pc) '
       '(Input|SetInputModeGameOnly :PlayerController pc) '+setv(g,'WorkshopOpen','false')+')')
    fn(inv,'ToggleWorkshop',lambda g:'(if '+get(g,'WorkshopOpen')+' ('+find(g,'CloseWorkshop')+') (else ('+find(g,'OpenWorkshop')+')))')
    def collect_nearby(g):
        return ('(if (not '+get(g,'WorkshopOpen')+') '+setv(g,'LastMessage',q('Подойди ближе к дереву или руде.'))+
        ' (bind player (Game|GetPlayerPawn)) (bind resources (Actor|GetAllActorsOfClass :ActorClass '+q(pickup.generated_class().get_path_name())+')) '
        '(for resource resources (if (< (Transformation|GetDistanceTo :self resource :OtherActor player) 210.0) ('+find(g,'Collect')+' :self resource) (break))) '
        '(Development|PrintString :InString '+get(g,'LastMessage')+' :Duration 2.0 :Key "ResourcePickup"))')
    fn(inv,'CollectNearby',collect_nearby)
    eg=B.get_graph(inv,'EventGraph')
    B.write_graph_dsl(eg,'(event AddEvent|EventBeginPlay (Input|EnableInput :self self :PlayerController (Game|GetPlayerController)) '+setv(eg,'LastMessage',q('Закрой мастерскую клавишей Tab. На карте подойди к ресурсу и нажми E.'))+' ('+find(eg,'OpenWorkshop')+'))')
    for key,method in [('E','CollectNearby'),('Tab','ToggleWorkshop')]:
        types=[str(n) for n in B.find_node_types(eg,'KeyboardEvents|'+key) if str(n)=='Input|KeyboardEvents|'+key]
        assert types,key
        event=B.create_node(eg,types[0],unreal.IntPoint(0,0))
        call=B.create_node(eg,find(eg,method),unreal.IntPoint(0,0))
        connect(event,'Pressed',call,'execute')
    B.arrange_nodes(B.find_nodes(eg)); save(inv)
    # Test map leaves the user's existing levels untouched.
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    map_path=ROOT+'/Lvl_ResourceWorkshop'
    assert not unreal.EditorAssetLibrary.does_asset_exist(map_path),'Demo map already exists'
    assert levels.new_level_from_template(map_path,'/Engine/Maps/Templates/Template_Default')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    gm=unreal.load_asset('/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode')
    world.get_world_settings().set_editor_property('default_game_mode',gm.generated_class())
    starts=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.PlayerStart)]
    start=starts[0] if starts else actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(0,0,120))
    start.set_actor_location(unreal.Vector(-600,0,150),False,False)
    start.set_actor_rotation(unreal.Rotator(0,0,0),False)
    controller=actors.spawn_actor_from_class(inv.generated_class(),unreal.Vector(0,0,50))
    controller.set_actor_label('Resource Workshop - inventory and input')
    for index in range(6):
        a=actors.spawn_actor_from_class(wood.generated_class(),unreal.Vector(-100+index*220,-330,55))
        a.set_actor_scale3d(unreal.Vector(.55,.55,1.1)); a.set_actor_label('Wood '+str(index+1))
    for index in range(4):
        a=actors.spawn_actor_from_class(ore.generated_class(),unreal.Vector(-100+index*240,330,55))
        a.set_actor_scale3d(unreal.Vector(.9,.75,.8)); a.set_actor_label('Iron ore '+str(index+1))
    for label,location in [('WOOD / E',unreal.Vector(-100,-330,160)),('IRON ORE / E',unreal.Vector(-100,330,160)),('TAB - WORKSHOP',unreal.Vector(-500,0,260))]:
        sign=actors.spawn_actor_from_class(unreal.TextRenderActor,location,unreal.Rotator(0,180,0))
        sign.text_render.set_text(label); sign.text_render.set_world_size(32)
    assert levels.save_current_level()
    log('MAP SAVED '+map_path)
    log('DONE')
