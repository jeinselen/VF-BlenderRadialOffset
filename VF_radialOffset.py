bl_info = {
	"name": "VF Radial Offset",
	"author": "John Einselen - Vectorform LLC",
	"version": (0, 3, 0),
	"blender": (2, 83, 0),
	"location": "Scene > VF Tools > Radial Offset",
	"description": "Radially offset vertices, maintaining relative distances",
	"warning": "inexperienced developer, use at your own risk",
	"doc_url": "https://github.com/jeinselenVF/VF-BlenderRadialOffset",
	"tracker_url": "https://github.com/jeinselenVF/VF-BlenderRadialOffset/issues",
	"category": "3D View"}

# Based in part on basic code found here:
# https://blenderartists.org/t/move-selected-vertices-with-python-script/1303114
# https://blender.stackexchange.com/questions/196483/create-keyboard-shortcut-for-an-operator-using-python

import bpy
from bpy.app.handlers import persistent
import mathutils
#import bmesh # Only used to get active vertex, the rest of the operations act on the mesh data directly

###########################################################################
# Main class

class vf_radial_offset(bpy.types.Operator):
	bl_idname = "vfradialoffset.offset"
	bl_label = "Apply Radial Offset"
	bl_description = "Radially offset vertices, maintaining relative distances"
	bl_options = {'REGISTER', 'UNDO'}
	
	def execute(self, context):
		if not context.view_layer.objects.active.data.vertices:
			return {'CANCELLED'}
		
		# Set up local variables
		offset = context.scene.vf_radial_offset_settings.offset_distance
		channels = mathutils.Vector((0.0 if offset[0] == 0.0 else 1.0, 0.0 if offset[1] == 0.0 else 1.0, 0.0 if offset[2] == 0.0 else 1.0))
		
		# Begin code modified from Scriblab and Photox source on BlenderArtist https://blenderartists.org/t/move-selected-vertices-with-python-script/1303114
		mode = context.active_object.mode
		bpy.ops.object.mode_set(mode='OBJECT')
		selectedVerts = [v for v in context.active_object.data.vertices if v.select]
		
		# Get specified offset starting point position
		if context.scene.vf_radial_offset_settings.offset_position == 'BOUNDING':
			minCo = selectedVerts[0].co.copy()
			maxCo = selectedVerts[0].co.copy()
			for vert in selectedVerts:
				minCo[0] = min(minCo[0], vert.co[0])
				minCo[1] = min(minCo[1], vert.co[1])
				minCo[2] = min(minCo[2], vert.co[2])
				maxCo[0] = max(maxCo[0], vert.co[0])
				maxCo[1] = max(maxCo[1], vert.co[1])
				maxCo[2] = max(maxCo[2], vert.co[2])
			point = ((maxCo - minCo) * 0.5) + minCo
#		elif context.scene.vf_radial_offset_settings.offset_position == 'ACTIVE':
#			bpy.ops.object.mode_set(mode='EDIT')
#			temp = bmesh.from_edit_mesh(bpy.context.active_object.data)
#			point = temp.select_history.active.co
#			bpy.ops.object.mode_set(mode='OBJECT')
		elif context.scene.vf_radial_offset_settings.offset_position == 'CUSTOM':
			point = context.scene.vf_radial_offset_settings.offset_position_custom
		elif context.scene.vf_radial_offset_settings.offset_position == 'CURSOR':
			point = context.scene.cursor.location
		else: # OBJECT
			point = mathutils.Vector((0.0, 0.0, 0.0))
		
		# Process vertices
		for vert in selectedVerts:
			new_location = vert.co
			radial_vector = ((vert.co - point) * channels).normalized()
			
			if offset[0] != 0.0:
				new_location[0] = new_location[0] + (radial_vector[0] * offset[0])
			if offset[1] != 0.0:
				new_location[1] = new_location[1] + (radial_vector[1] * offset[1])
			if offset[2] != 0.0:
				new_location[2] = new_location[2] + (radial_vector[2] * offset[2])
			vert.co = new_location
		
		# Reset object mode to original
		bpy.ops.object.mode_set(mode=mode)
		
		# Done
		return {'FINISHED'}

###########################################################################
# Project settings and UI rendering classes

class vfRadialOffsetSettings(bpy.types.PropertyGroup):
	offset_position: bpy.props.EnumProperty(
		name='Position',
		description='Centre point of the transform operation',
		items=[
			('OBJECT', 'Object', 'Offsets from the local mesh object root position'),
			('BOUNDING', 'Selection', 'Offsets from the middle of the selected vertices bounding box'),
#			('ACTIVE', 'Active Vertex', 'Offsets from the active vertex position'),
			('CUSTOM', 'Coordinates', 'Offsets using custom coordinates as the starting point'),
			('CURSOR', '3D Cursor', 'Scales using the 3D cursor position')
			],
		default='OBJECT')
	offset_position_custom: bpy.props.FloatVectorProperty(
		name="Custom",
		description="Position to scale from",
		subtype="TRANSLATION",
		default=[0.0, 0.0, 0.0],
		step=1.25,
		precision=3,
		soft_min=-1.0,
		soft_max=1.0)
	offset_distance: bpy.props.FloatVectorProperty(
		name="Offset",
		description="Radial offset without scaling distortion",
		subtype="TRANSLATION",
		default=[0.1, 0.1, 0.0],
		step=1.25,
		precision=3,
		soft_min=-1.0,
		soft_max=1.0)

class VFTOOLS_PT_radial_offset(bpy.types.Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'VF Tools'
	bl_order = 6
	bl_options = {'DEFAULT_CLOSED'}
	bl_label = "Radial Offset"
	bl_idname = "VFTOOLS_PT_radial_offset"
	
	@classmethod
	def poll(cls, context):
		return True
	
	def draw_header(self, context):
		try:
			layout = self.layout
		except Exception as exc:
			print(str(exc) + " | Error in VF Radial Offset panel header")
	
	def draw(self, context):
		try:
			layout = self.layout
			layout.use_property_split = True
			layout.use_property_decorate = False # No animation
			
			layout.prop(context.scene.vf_radial_offset_settings, 'offset_position')
			
			if context.scene.vf_radial_offset_settings.offset_position == "CUSTOM":
				col=layout.column()
				col.prop(context.scene.vf_radial_offset_settings, 'offset_position_custom')
			
			col=layout.column()
			col.prop(context.scene.vf_radial_offset_settings, 'offset_distance')
			
			# if context.view_layer.objects.active.data.vertices:
			if context.view_layer.objects.active and context.view_layer.objects.active.type == "MESH":
				layout.operator(vf_radial_offset.bl_idname)
			else:
				box = layout.box()
				box.label(text="Active object must be a mesh with selected vertices")
		except Exception as exc:
			print(str(exc) + " | Error in VF Radial Offset panel")

###########################################################################
# Addon registration functions

classes = (vf_radial_offset, vfRadialOffsetSettings, VFTOOLS_PT_radial_offset)

# addon_keymaps = []

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.Scene.vf_radial_offset_settings = bpy.props.PointerProperty(type=vfRadialOffsetSettings)
	
	# Add the hotkey
	# wm = bpy.context.window_manager
	# kc = wm.keyconfigs.addon
	# if kc:
		# km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
		# kmi = km.keymap_items.new(vf_radial_offset.bl_idname, type='Q', value='PRESS', shift=True)
		# addon_keymaps.append((km, kmi))

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	del bpy.types.Scene.vf_radial_offset_settings
	
	# Remove the hotkey
	# for km, kmi in addon_keymaps:
		# km.keymap_items.remove(kmi)
	# addon_keymaps.clear()

if __name__ == "__main__":
	register()