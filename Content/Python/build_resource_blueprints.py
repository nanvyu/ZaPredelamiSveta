"""Editor-only generator. All gameplay is stored as editable Blueprint nodes."""
import unreal, json
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as B

ROOT = '/Game/BlueprintResourcePrototype'
COUNTS = ['RawWood', 'WoodBlank', 'WoodGear', 'IronOre', 'CrushedOre', 'Charcoal', 'IronBlank', 'MetalGear']

def log(x): unreal.log('RESOURCE_BUILD ' + str(x))
def q(x): return json.dumps(x, ensure_ascii=False)
def node(graph, suffix):
    candidates = [str(n) for n in B.find_node_types(graph, suffix) if str(n).split('|')[-1].lower() == suffix.lower()]
    preferred = [n for n in candidates if n.startswith('Variables|') or n.startswith('Default|')]
    result = (preferred or candidates)
    assert result, (graph.get_name(), suffix)
    return result[0]
def get(graph, var): return '(' + node(graph, 'Get' + var) + ')'
def setv(graph, var, value): return '(' + node(graph, 'Set' + var) + ' ' + value + ')'
def function(bp, name, body):
    graph = B.add_function_graph(bp, name)
    code = '(fn ' + name + ' () ' + body(graph) + ')'
    B.write_graph_dsl(graph, code)
    B.arrange_nodes(B.find_nodes(graph))
    log('FUNCTION ' + name)

with toolset_registry.tool_raising_exceptions():
    bp = unreal.load_asset(ROOT + '/BP_ResourceInventory')
    if not bp: bp = B.create(ROOT, 'BP_ResourceInventory', unreal.Actor.static_class())
    existing = [str(x) for x in B.list_variables(bp)]
    for name in COUNTS + ['LabRepaired', 'LastMessage']:
        if name not in existing:
            B.add_variable(bp, name, 'bool' if name == 'LabRepaired' else 'string' if name == 'LastMessage' else 'int')
    B.compile_blueprint(bp)
    for name, var, message in [('CollectWood','RawWood','Подобрана древесина.'), ('CollectOre','IronOre','Подобрана железная руда.')]:
        function(bp, name, lambda g, v=var, m=message: setv(g,v,'(+ '+get(g,v)+' 1)') + setv(g,'LastMessage',q(m)))
    recipes = [
        ('SawWood', {'RawWood':1}, {'WoodBlank':2}, 'Распил: получены 2 деревянные заготовки.'),
        ('CarveWoodGear', {'WoodBlank':2}, {'WoodGear':1}, 'Вырезана деревянная шестерёнка для тихоходного привода.'),
        ('MakeCharcoal', {'RawWood':2}, {'Charcoal':1}, 'Пиролиз без доступа воздуха: получен древесный уголь.'),
        ('CrushOre', {'IronOre':1}, {'CrushedOre':1}, 'Руда раздроблена и подготовлена к плавке.'),
        ('SmeltIron', {'CrushedOre':2,'Charcoal':1}, {'IronBlank':1}, 'В печи получена железная заготовка. Время процесса условно сокращено.'),
        ('ForgeMetalGear', {'IronBlank':1}, {'MetalGear':1}, 'Заготовка выкована и обработана: металлическая шестерёнка готова.'),
    ]
    for name, costs, outputs, message in recipes:
        def body(g, costs=costs, outputs=outputs, message=message):
            checks = ['(>= '+get(g,v)+' '+str(n)+')' for v,n in costs.items()]
            condition = checks[0] if len(checks)==1 else '(and '+' '.join(checks)+')'
            success = ''.join(setv(g,v,'(- '+get(g,v)+' '+str(n)+')') for v,n in costs.items())
            success += ''.join(setv(g,v,'(+ '+get(g,v)+' '+str(n)+')') for v,n in outputs.items())
            return '(if '+condition+' '+success+setv(g,'LastMessage',q(message))+' (else '+setv(g,'LastMessage',q('Недостаточно ресурсов. Проверь рецепт.'))+'))'
        function(bp, name, body)
    def repair(g):
        return '(if '+get(g,'LabRepaired')+' '+setv(g,'LastMessage',q('Лаборатория уже отремонтирована. Рация доступна.'))+' (else (if (and (>= '+get(g,'WoodGear')+' 1) (>= '+get(g,'MetalGear')+' 1)) '+setv(g,'WoodGear','(- '+get(g,'WoodGear')+' 1)')+setv(g,'MetalGear','(- '+get(g,'MetalGear')+' 1)')+setv(g,'LabRepaired','true')+setv(g,'LastMessage',q('Привод лаборатории восстановлен! Рация доступна.'))+' (else '+setv(g,'LastMessage',q('Для ремонта нужны деревянная и металлическая шестерёнки.'))+'))))'
    function(bp, 'RepairLab', repair)
    function(bp, 'UseRadio', lambda g: '(if '+get(g,'LabRepaired')+' '+setv(g,'LastMessage',q('Связь установлена: «База, лаборатория восстановлена. Приём!»'))+' (else '+setv(g,'LastMessage',q('Сначала восстанови привод лаборатории.'))+'))')
    B.compile_blueprint(bp, True)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    log('INVENTORY SAVED')
    # Discover existing widget hierarchy without modifying the original assets.
    log('ITER API '+str([x for x in dir(unreal) if 'Iterator' in x or 'objects' in x.lower()]))
    for path in ['/Game/Widgets/BP_Workshop', '/Game/Widgets/BP_Machine_engine']:
        wbp = unreal.load_asset(path)
        tree = unreal.find_object(wbp, 'WidgetTree')
        for name in ['CanvasPanel_0','CanvasPanel','Root','Image_0','Image_1','Button_0','Overlay_0']:
            obj = unreal.find_object(tree,name)
            if obj:
                log('FOUND '+obj.get_path_name()+' '+obj.get_class().get_name())
                if isinstance(obj,unreal.PanelWidget):
                    def visit(w):
                        log('WIDGET '+w.get_name()+' '+w.get_class().get_name())
                        if isinstance(w,unreal.PanelWidget):
                            for c in w.get_all_children(): visit(c)
                    visit(obj)
    log('DONE')
