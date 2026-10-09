"""Build the editable UMG screen and bind buttons to Blueprint recipe functions."""
import unreal, json
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as B
ROOT='/Game/BlueprintResourcePrototype'
def log(x): unreal.log('RESOURCE_SCREEN '+str(x))
def q(x): return json.dumps(x,ensure_ascii=False)
def find(g,suffix):
    matches=[str(n) for n in B.find_node_types(g,suffix) if str(n).split('|')[-1].lower()==suffix.lower()]
    assert matches,(g.get_name(),suffix)
    return next((n for n in matches if n.startswith('Variables|')),matches[0])
def get(g,v): return '('+find(g,'Get'+v)+')'
def foreign_get(g,v):
    matches=[str(n) for n in B.find_node_types(g,'Get'+v) if 'BPResourceInventory|' in str(n) and str(n).endswith('|Get'+v)]
    assert matches, ('external',v, list(B.find_node_types(g,'Get'+v)))
    return '('+matches[0]+' :self '+get(g,'Inventory')+')'
def fn(bp,name,body):
    g=B.add_function_graph(bp,name)
    B.write_graph_dsl(g,'(fn '+name+' () '+body(g)+')')
    B.arrange_nodes(B.find_nodes(g))
    log('FUNCTION '+name)
def link(a,out,b,inp):
    pa=unreal.BlueprintEditorLibrary.find_output_pin(a,out)
    pb=unreal.BlueprintEditorLibrary.find_input_pin(b,inp)
    assert pa.try_create_connection(pb), (out,inp)
def make_node(g,name): return B.create_node(g,name,unreal.IntPoint(0,0))
def default(n,p,v):
    assert unreal.BlueprintEditorLibrary.find_input_pin(n,p).set_pin_value(v),(p,v)

with toolset_registry.tool_raising_exceptions():
    inventory=unreal.load_asset(ROOT+'/BP_ResourceInventory')
    destination=ROOT+'/WBP_ResourceWorkshop'
    assert not unreal.EditorAssetLibrary.does_asset_exist(destination),'Screen already exists; inspect before rebuilding.'
    bp=unreal.EditorAssetLibrary.duplicate_asset('/Game/Input/Touch/UI_TouchSimple',destination)
    tree=unreal.find_object(bp,'WidgetTree')
    roots=[w for w in unreal.ObjectIterator(unreal.PanelWidget) if w.get_outer()==tree and w.get_parent() is None]
    assert len(roots)==1, roots
    root=roots[0]
    root.clear_children()
    eg=B.get_graph(bp,'EventGraph')
    for n in list(B.find_nodes(eg)): B.delete_node(n)
    for var in list(B.list_variables(bp)): B.remove_variable(bp,str(var))

    def new(cls,name,variable=False):
        w=unreal.new_object(cls,tree,name)
        return w
    scale=new(unreal.ScaleBox,'ScreenScale')
    sl=root.add_child_to_overlay(scale)
    sl.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL)
    sl.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_FILL)
    size=new(unreal.SizeBox,'DesignSize'); size.set_width_override(1600); size.set_height_override(900)
    scale.add_child(size)
    canvas=new(unreal.CanvasPanel,'CraftingCanvas'); size.add_child(canvas)
    def place(w,x,y,width,height):
        slot=canvas.add_child_to_canvas(w)
        slot.set_position(unreal.Vector2D(x,y)); slot.set_size(unreal.Vector2D(width,height))
        return w
    def label(name,text,x,y,width,height,font=24,variable=False):
        w=new(unreal.RichTextBlock if variable else unreal.TextBlock,name,variable)
        w.set_text(text)
        if variable:
            w.set_default_font(unreal.SlateFontInfo(font_object=unreal.load_object(None,'/Engine/EngineFonts/Roboto.Roboto'),size=font))
            w.set_default_color_and_opacity(unreal.SlateColor(specified_color=unreal.LinearColor(.91,.94,.91,1)))
        else:
            f=w.get_editor_property('font'); f.set_editor_property('size',font); w.set_font(f)
            w.set_color_and_opacity(unreal.SlateColor(specified_color=unreal.LinearColor(.91,.94,.91,1)))
        w.set_auto_wrap_text(True)
        return place(w,x,y,width,height)
    bg=new(unreal.Border,'Background'); bg.set_brush_color(unreal.LinearColor(.018,.029,.038,.98)); place(bg,0,0,1600,900)
    label('Title','ПОЛЕВАЯ МАСТЕРСКАЯ',40,25,1250,55,34)
    label('Subtitle','Собери материалы → обработай → восстанови привод мобильной лаборатории',40,88,1460,42,22)
    art=new(unreal.WidgetSwitcher,'StationArt',True); place(art,40,155,930,445)
    for index,source in enumerate(['/Game/Widgets/BP_Workshop','/Game/Widgets/BP_Machine_engine']):
        user_widget=unreal.new_object(unreal.load_asset(source).generated_class(),tree,'ExistingArt'+str(index))
        art.add_child(user_widget)
    label('ArtCaption','Исходные экраны проекта: дерево / камень',40,610,920,35,20)
    label('StockTitle','РЮКЗАК',1020,155,530,40,28)
    label('InventoryText','Ресурсы появятся после сбора на карте.',1020,212,540,340,24,True)
    label('MessageText','Подойди к ресурсам на карте и нажми E.',1020,575,525,155,24,True)
    label('Hint','Tab — закрыть мастерскую. На карте: WASD — движение, E — подобрать рядом.',40,850,1490,35,20)
    actions=[
        ('SawWood','Распилить: 1 дерево → 2 заготовки',40,655,450),
        ('CarveWoodGear','Вырезать: 2 заготовки → шестерёнка',515,655,450),
        ('MakeCharcoal','Пиролиз: 2 дерева → 1 уголь',40,720,450),
        ('CrushOre','Дробление: 1 руда → 1 дроблёная',515,720,450),
        ('SmeltIron','Плавка: 2 руды + 1 уголь → железо',40,785,450),
        ('ForgeMetalGear','Обработка железа → шестерёнка',515,785,450),
        ('RepairLab','Ремонт: 2 разные шестерёнки',1020,735,530),
        ('UseRadio','Связаться с базой',1020,800,530),
        ('ShowWood','Дерево',40,130,200),
        ('ShowOre','Руда',265,130,200),
    ]
    for name,text,x,y,width in actions:
        button=new(unreal.Button,'Btn_'+name,True)
        button.set_editor_property('is_focusable',False)
        button.set_background_color(unreal.LinearColor(.13,.28,.27,1))
        txt=new(unreal.TextBlock,'Label_'+name)
        txt.set_text(text)
        font=txt.get_editor_property('font'); font.set_editor_property('size',19); txt.set_font(font)
        button.add_child(txt)
        place(button,x,y,width,50 if name not in ['ShowWood','ShowOre'] else 30)
    B.add_object_variable(bp,'Inventory',inventory.generated_class())
    B.compile_blueprint(bp)
    log('DESIGNER READY')
    # Resolve foreign inventory access using the graph's available node list.
    log('INVENTORY NODES '+str(list(B.find_node_types(eg,'RawWood'))))
    log('FUNCTION NODES '+str(list(B.find_node_types(eg,'SawWood'))))
    text_setter=None
    for candidate in B.find_node_types(eg,'SetText'):
        if 'SetText' == str(candidate).split('|')[-1] or 'SetText(' in str(candidate):
            info=B.get_node_type_pins(eg,candidate)
            if any(p.name=='self' and 'Rich Text Block' in p.type_id for p in info.input_pins):
                text_setter=str(candidate); break
    assert text_setter, 'RichTextBlock SetText not found'
    def refresh_body(g):
        append=next(str(n) for n in B.find_node_types(g,'Append') if str(n)=='Utilities|String|Append')
        to_string=find(g,'ToString(Integer)')
        text=q('')
        for label,var in [('Древесина','RawWood'),('Заготовки','WoodBlank'),('Деревянные шестерёнки','WoodGear'),('Железная руда','IronOre'),('Дроблёная руда','CrushedOre'),('Древесный уголь','Charcoal'),('Железные заготовки','IronBlank'),('Металлические шестерёнки','MetalGear')]:
            line='('+append+' :A '+q(label+': ')+' :B ('+to_string+' '+foreign_get(g,var)+'))'
            text='('+append+' :A '+text+' :B ('+append+' :A '+line+' :B '+q('\n')+'))'
        return '('+text_setter+' :self '+get(g,'InventoryText')+' :InText '+text+') ('+text_setter+' :self '+get(g,'MessageText')+' :InText '+foreign_get(g,'LastMessage')+')'
    fn(bp,'RefreshInventory',refresh_body)
    for name,*_ in actions:
        if name in ['ShowWood','ShowOre']:
            fn(bp,'Click_'+name,lambda g,i=0 if name=='ShowWood' else 1:'(Switcher|SetActiveWidgetIndex :self '+get(g,'StationArt')+' :Index '+str(i)+')')
        else:
            fn(bp,'Click_'+name,lambda g,name=name:'('+find(g,name)+' :self '+get(g,'Inventory')+') ('+find(g,'RefreshInventory')+')')
    # Construct: resolve inventory, bind buttons to named functions, refresh once.
    begin=B.add_event(bp,'Construct')
    lookup=make_node(eg,'Actor|GetActorOfClass'); default(lookup,'ActorClass',inventory.generated_class().get_path_name())
    link(begin,'then',lookup,'execute')
    store=make_node(eg,find(eg,'SetInventory')); link(lookup,'then',store,'execute'); link(lookup,'ReturnValue',store,'Inventory')
    tail=store
    for name,*_ in actions:
        getter=make_node(eg,find(eg,'GetBtn_'+name))
        bind=make_node(eg,'Button|Event|BindEventtoOnClicked')
        delegate=make_node(eg,'EventDispatchers|CreateEvent')
        link(getter,'Btn_'+name,bind,'self'); link(delegate,'OutputDelegate',bind,'Delegate')
        B.set_create_event_function(delegate,'Click_'+name)
        link(tail,'then',bind,'execute'); tail=bind
    refresh=make_node(eg,find(eg,'RefreshInventory')); link(tail,'then',refresh,'execute')
    B.arrange_nodes(B.find_nodes(eg))
    B.compile_blueprint(bp,True)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    log('SCREEN SAVED')
