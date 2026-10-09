"""PIE integration test for the Blueprint resource prototype."""
import unreal, time, traceback
ROOT='/Game/BlueprintResourcePrototype'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.load_level(ROOT+'/Lvl_ResourceWorkshop')
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
started=time.monotonic()
state={'step':0,'frames':0,'handle':None}
def log(message): unreal.log('RESOURCE_PLAY '+message)
def finish():
    unreal.unregister_slate_post_tick_callback(state['handle'])
    levels.editor_request_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(delta):
    state['frames']+=1
    if time.monotonic()-started>100:
        unreal.log_error('RESOURCE_PLAY FAIL timeout'); finish(); return
    try:
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if not world: return
        inv_class=unreal.load_asset(ROOT+'/BP_ResourceInventory').generated_class()
        inv=unreal.GameplayStatics.get_actor_of_class(world,inv_class)
        if not inv: return
        def val(v): return inv.get_editor_property(v)
        def call(f): inv.call_method(f)
        if state['step']==0:
            ui=val('Workshop')
            if not ui or not ui.is_in_viewport(): return
            assert val('WorkshopOpen')
            assert ui.get_editor_property('Inventory')==inv
            stock=ui.get_editor_property('InventoryText')
            assert stock and '0' in str(stock.get_text()),str(stock)
            assert len(str(stock.get_text()).splitlines())==8,str(stock.get_text())
            assert '\\n' not in str(stock.get_text()),str(stock.get_text())
            for v in ['RawWood','IronOre','WoodGear','MetalGear']: assert val(v)==0
            ui.call_method('Click_SawWood'); assert val('WoodBlank')==0
            ui.call_method('Click_RepairLab'); assert not val('LabRepaired')
            ui.call_method('Click_UseRadio'); assert not val('LabRepaired')
            log('PASS initial UI / insufficient resources / locked radio')
            call('CloseWorkshop'); assert not val('WorkshopOpen') and not ui.is_in_viewport()
            player=unreal.GameplayStatics.get_player_pawn(world,0); assert player
            player.set_actor_location(unreal.Vector(-600,0,150),False,False)
            call('CollectNearby'); assert val('RawWood')==0 and val('IronOre')==0
            wood_class=unreal.load_asset(ROOT+'/BP_WoodPickup').generated_class()
            ore_class=unreal.load_asset(ROOT+'/BP_IronOrePickup').generated_class()
            for cls,count in [(wood_class,3),(ore_class,2)]:
                pickups=list(unreal.GameplayStatics.get_all_actors_of_class(world,cls))
                for pickup in pickups[:count]:
                    pos=pickup.get_actor_location()
                    player.set_actor_location(unreal.Vector(pos.x-40,pos.y,pos.z+90),False,False)
                    call('CollectNearby')
            assert val('RawWood')==3 and val('IronOre')==2,(val('RawWood'),val('IronOre'))
            log('PASS pickup distance / resource collection')
            call('OpenWorkshop'); ui=val('Workshop')
            assert ui and ui.is_in_viewport()
            ui.call_method('Click_ShowOre'); assert ui.get_editor_property('StationArt').get_active_widget_index()==1
            ui.call_method('Click_ShowWood'); assert ui.get_editor_property('StationArt').get_active_widget_index()==0
            for method in ['SawWood','CarveWoodGear','MakeCharcoal','CrushOre','CrushOre','SmeltIron','ForgeMetalGear','RepairLab','RepairLab','UseRadio']:
                ui.call_method('Click_'+method)
            assert val('LabRepaired')
            for v in ['RawWood','WoodBlank','WoodGear','IronOre','CrushedOre','Charcoal','IronBlank','MetalGear']: assert val(v)==0,(v,val(v))
            assert 'База' in str(ui.get_editor_property('MessageText').get_text())
            call('CloseWorkshop'); call('OpenWorkshop'); assert val('LabRepaired')
            log('PASS UI recipe chain / no negative inventory / repeat repair / reopen / radio')
            state['step']=1; state['frames']=0
        elif state['step']==1 and state['frames']>20:
            unreal.SystemLibrary.execute_console_command(world,'Shot showui')
            log('SCREENSHOT REQUESTED')
            state['step']=2; state['frames']=0
        elif state['step']==2 and state['frames']>20:
            log('ALL TESTS PASSED')
            finish()
    except Exception:
        unreal.log_error('RESOURCE_PLAY FAIL '+traceback.format_exc()); finish()
state['handle']=unreal.register_slate_post_tick_callback(tick)
levels.editor_request_begin_play()
log('PIE REQUESTED')
