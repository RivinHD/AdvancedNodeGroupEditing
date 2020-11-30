import bpy
from bpy.types import Panel, PropertyGroup, AddonPreferences, UIList
from bpy.props import EnumProperty

bl_info = {
    "name" : "Advanced NodeGroup Editing",
    "author" : "Rivin",
    "description" : "Allows you to edit futher parts of node group I/O",
    "blender" : (2, 83, 9),
    "version" : (0, 0, 1),
    "location" : "Node > UI > Node",
    "category" : "Node"
}

classes = []

def getPort(active, tree=None):
    if tree == None:
        tree = active
    port = None
    if tree.active_output != -1:
        Nout = tree.active_output
        port = active.outputs[Nout]
    elif tree.active_input != -1:
        Nin = tree.active_input
        port = active.inputs[Nin]
    return port

class ANGE_UL_Ports(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text= item.name)
classes.append(ANGE_UL_Ports)

class ANGE_PT_AdvancedEdit(bpy.types.Panel):
    bl_idname = "ANGE.ANGE_PT_advancededit"
    bl_label = "Advanced"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Node"

    @classmethod
    def poll(cls, context):
        active = bpy.context.object.active_material.node_tree.nodes.active
        return active.type == 'GROUP' and (active.node_tree.active_output != -1 or active.node_tree.active_input != -1)

    def draw(self, context):
        layout = self.layout
        ANGE = context.preferences.addons[__name__].preferences
        active = bpy.context.object.active_material.node_tree.nodes.active.node_tree    
        if not bpy.ops.node.tree_path_parent.poll():
            row = layout.row()
            col = row.column()
            col.label(text= 'Input:')
            col.template_list('ANGE_UL_Ports', '', active, 'inputs', active, 'active_input')
            col = row.column()
            col.label(text= 'Output:')
            col.template_list('ANGE_UL_Ports', '', active, 'outputs', active, 'active_output')
        layout.prop(ANGE, 'NodeType')
        layout.operator(ANGE_OT_Apply.bl_idname, text= 'Apply')
classes.append(ANGE_PT_AdvancedEdit)

class ANGE_OT_Apply(bpy.types.Operator):
    bl_idname = "ange.apply"
    bl_label = "Apply"
    bl_description = "Apply changes"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        active = bpy.context.object.active_material.node_tree.nodes.active
        return active.type == 'GROUP' and (active.node_tree.active_output != -1 or active.node_tree.active_input != -1)

    def execute(self, context):
        ANGE = context.preferences.addons[__name__].preferences
        active = context.object.active_material.node_tree.nodes.active
        port = getPort(active, active.node_tree)
        exec('port.type = ANGE.NodeType')
        return {"FINISHED"}
classes.append(ANGE_OT_Apply)

def ItemsTypes(scene, context):
    l = []
    node = context.object.active_material.node_tree.nodes.active
    if hasattr(node, 'node_tree'):
        active = node.node_tree
        port = getPort(active)
        if port != None:
            for prop in port.bl_rna.properties['type'].enum_items:
                l.append((prop.identifier, prop.name, prop.description, prop.icon, prop.value))
    return l

class ANGE_Prop(AddonPreferences):
    bl_idname = __name__

    NodeType : EnumProperty(items= ItemsTypes, name='Type', description= 'Data type')
classes.append(ANGE_Prop)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
