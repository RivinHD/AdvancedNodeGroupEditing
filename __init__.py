import bpy
from bpy.types import Panel, PropertyGroup, AddonPreferences, UIList, Operator
from bpy.props import EnumProperty, StringProperty

bl_info = {
    "name" : "Advanced NodeGroup Editing",
    "author" : "Rivin",
    "description" : "Allows you to edit futher parts of node group I/O",
    "blender" : (2, 83, 9),
    "version" : (1, 0, 3),
    "location" : "Node > UI > Node",
    "category" : "Node"
}

classes = []

def getPort(active):
    if active.active_output != -1:
        index = active.active_output
        socketTyp = active.outputs
    elif active.active_input != -1:
        index = active.active_input
        socketTyp = active.inputs
    return (socketTyp[index], socketTyp, index)

def FindNodeOfSocket(nodes, Type):
    for node in nodes:
        if node.type == 'GROUP_' + Type:
            return node

def getDefaultSocket(active, port, index):
    portType = 'OUTPUT' if port.is_output else 'INPUT'
    node = FindNodeOfSocket(active.nodes, portType)
    if portType == 'OUTPUT':
        nodePort = node.inputs[index]
    else:
        nodePort = node.outputs[index]
    return nodePort.bl_idname

class ANGE_UL_Ports(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text= item.name)
classes.append(ANGE_UL_Ports)

class ANGE_PT_AdvancedEdit(Panel):
    bl_idname = "ANGE_PT_AdvancedEdit"
    bl_label = "Advanced"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Node"

    @classmethod
    def poll(cls, context):
        active = bpy.context.object.active_material.node_tree.nodes.active
        if bpy.ops.node.tree_path_parent.poll():
            access = (active.node_tree.active_output != -1 or active.node_tree.active_input != -1)
        else:
            access = True
        return active != None and active.type == 'GROUP' and access

    def draw(self, context):
        layout = self.layout
        ANGE = context.preferences.addons[__name__].preferences
        activeNode = context.object.active_material.node_tree.nodes.active
        active = activeNode.node_tree    
        if not bpy.ops.node.tree_path_parent.poll():
            row = layout.row()
            col = row.column()
            col.label(text= 'Input:')
            col.template_list('ANGE_UL_Ports', '', active, 'inputs', active, 'active_input')
            col = row.column()
            col.label(text= 'Output:')
            col.template_list('ANGE_UL_Ports', '', active, 'outputs', active, 'active_output')
            port, socket, index = getPort(active)
            if port.is_output:
                layout.prop(activeNode.outputs[index], 'default_value')
            else:
                layout.prop(activeNode.inputs[index], 'default_value')
            if hasattr(port, 'min_value'):
                row = layout.row(align= True)
                row.prop(port, 'min_value') 
                row.prop(port, 'max_value')
        row = layout.row(align= True)
        col = row.column(align= True)
        col.scale_x = 3
        col.prop(ANGE, 'NodeSockets', text= "Socket")
        row.operator(ANGE_OT_GetTypeOfSelected.bl_idname, text= '', icon= 'EYEDROPPER')
        layout.operator(ANGE_OT_Apply.bl_idname, text= 'Apply')
classes.append(ANGE_PT_AdvancedEdit)

class ANGE_OT_GetTypeOfSelected(Operator):
    bl_idname = "ange.get_type_of_selected"
    bl_label = "Get Type of Selected"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        active = bpy.context.object.active_material.node_tree.nodes.active
        if bpy.ops.node.tree_path_parent.poll():
            access = (active.node_tree.active_output != -1 or active.node_tree.active_input != -1)
        else:
            access = True
        return active != None and active.type == 'GROUP' and access

    def execute(self, context):
        ANGE = context.preferences.addons[__name__].preferences
        active = bpy.context.object.active_material.node_tree.nodes.active.node_tree
        port, socket, index = getPort(active)
        ANGE.NodeSockets = getDefaultSocket(active, port, index)
        return {"FINISHED"}
classes.append(ANGE_OT_GetTypeOfSelected)

class ANGE_OT_Apply(Operator):
    bl_idname = "ange.apply"
    bl_label = "Apply"
    bl_description = "Apply changes"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        active = bpy.context.object.active_material.node_tree.nodes.active
        if bpy.ops.node.tree_path_parent.poll():
            access = (active.node_tree.active_output != -1 or active.node_tree.active_input != -1)
        else:
            access = True
        return active != None and active.type == 'GROUP' and access

    def execute(self, context):
        ANGE = context.preferences.addons[__name__].preferences
        activeNode = context.object.active_material.node_tree.nodes.active
        active = activeNode.node_tree
        port, socket, index = getPort(active)
        socketType = ANGE.NodeSockets

        #Copy Data
        new = socket.new(socketType, port.name)
        default = eval("bpy.types." + socketType + ".bl_rna.properties['default_value']")
        try:
            if port.is_output:
                activeNode.outputs[-1].default_value = activeNode.outputs[index].default_value
            else:
                activeNode.inputs[-1].default_value = activeNode.inputs[index].default_value
        except:
            if default.is_array:
                new.default_value = default.default_array
            else:
                new.default_value = default.default
        try:
            new.min_value = port.min_value
            new.max_value = port.max_value
        except:
            if hasattr(new, 'min_value'):
                new.min_value = default.soft_min
                new.max_value = default.soft_max

        # Copy Links
        portType = 'OUTPUT' if new.is_output else 'INPUT'
        node = FindNodeOfSocket(active.nodes, portType)
        if portType == 'OUTPUT':
            nodeSocket = node.inputs
            nodePort = nodeSocket[index]
            for link in nodePort.links:
                active.links.new(nodeSocket[-2], link.from_socket)
        else:
            nodeSocket = node.outputs
            nodePort = nodeSocket[index]
            for link in nodePort.links:
                active.links.new(link.to_socket, nodeSocket[-2])

        # Move Socket 
        socket.move(len(socket) - 1, index)
        socket.remove(port)
        if portType == 'OUTPUT':
            active.active_output = index
        else:
            active.active_input = index
        return {"FINISHED"}
classes.append(ANGE_OT_Apply)



class ANGE_Prop(AddonPreferences):
    bl_idname = __name__
    SocketItems = [('NodeSocketBool','Bool','boolean'),
                    ('NodeSocketString', 'String', 'string'),
                    ('NodeSocketFloat', 'Float', 'float in [-inf, inf]'),
                    ('NodeSocketFloatAngle', 'Float (Angle)', 'float in [-inf, inf]'),
                    ('NodeSocketFloatFactor', 'Float (Factor)', 'float in [0, 1]'),
                    ('NodeSocketFloatPercentage', 'Float (Percentage)', 'float in [-inf, inf]'),
                    ('NodeSocketFloatTime', 'Float (Time)', 'float in [-inf, inf]'),
                    ('NodeSocketFloatUnsigned', 'Float (Unsigned)', 'float in [0, inf]'),
                    ('NodeSocketInt', 'Int', 'int in [-inf, inf]'),
                    ('NodeSocketIntFactor', 'Int (Factor)', 'int in [0, inf]'),
                    ('NodeSocketIntPercentage', 'Int (Percentage)', 'int in [0, inf]'),
                    ('NodeSocketIntUnsigned', 'Int (Unsigned)', 'int in [0, inf]'),
                    ('NodeSocketVector', 'Vector', 'float array of 3 items in [-inf, inf]'),
                    ('NodeSocketVectorAcceleration', 'Vector (Acceleration)', 'float array of 3 items in [-inf, inf]'),
                    ('NodeSocketVectorDirection', 'Vector (Direction)', 'float array of 3 items in [-inf, inf]'),
                    ('NodeSocketVectorEuler', 'Vector (Euler)', 'float array of 3 items in [-inf, inf]'),
                    ('NodeSocketVectorTranslation', 'Vector (Translation)', 'float array of 3 items in [-inf, inf]'),
                    ('NodeSocketVectorVelocity', 'Vector (Velocity)', 'float array of 3 items in [-inf, inf]'),
                    ('NodeSocketVectorXYZ', 'Vector (XYZ)', 'float array of 3 items in [-inf, inf]'),
                    ('NodeSocketColor', 'Color', 'float array of 4 items in [0, inf]'),
                    ('NodeSocketImage', 'Image', 'type Image'),
                    ('NodeSocketShader', 'Shader', ''),
                    ('NodeSocketObject', 'Object', 'type Object')]
    NodeSockets : EnumProperty(items= SocketItems, name='Sockets', description='All available Sockets for a Node')
classes.append(ANGE_Prop)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("-- Registered Advanced NodeGroup Editing --")

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    print("-- Unregistered Advanced NodeGroup Editing --")