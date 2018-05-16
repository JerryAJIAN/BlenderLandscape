import bpy
import os

def assignmatslots(ob, matlist):
    #given an object and a list of material names
    #removes all material slots form the object
    #adds new ones for each material in matlist
    #adds the materials to the slots as well.

    scn = bpy.context.scene
    ob_active = bpy.context.active_object
    scn.objects.active = ob

    for s in ob.material_slots:
        bpy.ops.object.material_slot_remove()

    # re-add them and assign material
    i = 0
    for m in matlist:
        mat = bpy.data.materials[m]
        ob.data.materials.append(mat)
        bpy.context.object.active_material.use_transparency = True
        bpy.context.object.active_material.alpha = 0.5
        i += 1

    # restore active object:
    scn.objects.active = ob_active


def check_texture(img, mat):
    #finds a texture from an image
    #makes a texture if needed
    #adds it to the material if it isn't there already

    tex = bpy.data.textures.get(img.name)

    if tex is None:
        tex = bpy.data.textures.new(name=img.name, type='IMAGE')

    tex.image = img

    #see if the material already uses this tex
    #add it if needed
    found = False
    for m in mat.texture_slots:
        if m and m.texture == tex:
            found = True
            break
    if not found and mat:
        mtex = mat.texture_slots.add()
        mtex.texture = tex
        mtex.texture_coords = 'UV'
        mtex.use_map_color_diffuse = True

def tex_to_mat():
    # editmode check here!
    editmode = False
    ob = bpy.context.object
    if ob.mode == 'EDIT':
        editmode = True
        bpy.ops.object.mode_set()

    for ob in bpy.context.selected_editable_objects:

        faceindex = []
        unique_images = []

        # get the texface images and store indices
        if (ob.data.uv_textures):
            for f in ob.data.uv_textures.active.data:
                if f.image:
                    img = f.image
                    #build list of unique images
                    if img not in unique_images:
                        unique_images.append(img)
                    faceindex.append(unique_images.index(img))

                else:
                    img = None
                    faceindex.append(None)

        # check materials for images exist; create if needed
        matlist = []
        for i in unique_images:
            if i:
                try:
                    m = bpy.data.materials[i.name]
                except:
                    m = bpy.data.materials.new(name=i.name)
                    continue

                finally:
                    matlist.append(m.name)
                    # add textures if needed
                    check_texture(i, m)

        # set up the object material slots
        assignmatslots(ob, matlist)

        #set texface indices to material slot indices..
        me = ob.data

        i = 0
        for f in faceindex:
            if f is not None:
                me.polygons[i].material_index = f
            i += 1
    if editmode:
        bpy.ops.object.mode_set(mode='EDIT')



class VIEW3D_OT_tex_to_material(bpy.types.Operator):
    """Create texture materials for images assigned in UV editor"""
    bl_idname = "view3d.tex_to_material"
    bl_label = "Texface Images to Material/Texture (Material Utils)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        if context.selected_editable_objects:
            tex_to_mat()
            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "No editable selected objects, could not finish")
            return {'CANCELLED'}


class ToolsPanel5(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
#    bl_context = "objectmode"
    bl_category = "BL"
    bl_label = "Photogrammetry tool"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.object

        obj_selected = scene.objects.active
        row = layout.row()
        row.label(text="Set up scene", icon='RADIO')
        row = layout.row()
        self.layout.operator("correct.material", icon="NODE", text='Correct Photoscan mats')
        self.layout.operator("isometric.scene", icon="RENDER_REGION", text='Isometric scene')
        self.layout.operator("canon6d.scene", icon="RENDER_REGION", text='CANON 6D scene')
        row = layout.row()
        row.label(text="Set selected cams as:", icon='RENDER_STILL')
        self.layout.operator("canon6d35mm.camera", icon="RENDER_REGION", text='Canon6D 35mm')
        self.layout.operator("canon6d24mm.camera", icon="RENDER_REGION", text='Canon6D 24mm')
        self.layout.operator("canon6d14mm.camera", icon="RENDER_REGION", text='Canon6D 14mm')
        row = layout.row()
        row.label(text="Visual mode for selected cams:", icon='NODE_SEL')
        self.layout.operator("better.cameras", icon="NODE_SEL", text='Better Cams')
        self.layout.operator("nobetter.cameras", icon="NODE_SEL", text='Disable Better Cams')
        row = layout.row()
        row = layout.row()
        row.label(text="Painting Toolbox", icon='TPAINT_HLT')
        row = layout.row()
        row.label(text="Folder with undistorted images:")
        row = layout.row()
        row.prop(context.scene, 'BL_undistorted_path', toggle = True)
        row = layout.row()

        if bpy.context.scene.camera is not None:
            cam_ob = scene.camera
            cam_cam = scene.camera.data
            row.label(text="Active Cam: " + cam_ob.name)
            self.layout.operator("object.createcameraimageplane", icon="IMAGE_COL", text='Photo to camera')
            row = layout.row()
            row = layout.row()
            row.prop(cam_cam, "lens")
            row = layout.row()
            row.label(text="Active object: " + obj.name)
            self.layout.operator("paint.cam", icon="IMAGE_COL", text='Paint active from cam')
            self.layout.operator("applypaint.cam", icon="IMAGE_COL", text='Apply paint')
            self.layout.operator("savepaint.cam", icon="IMAGE_COL", text='Save modified texs')
            row = layout.row()
        else:
            row.label(text="!!! Import some cams to start !!!")

#        self.layout.operator("cam.visibility", icon="RENDER_REGION", text='Cam visibility')

class OBJECT_OT_CorrectMaterial(bpy.types.Operator):
    bl_idname = "correct.material"
    bl_label = "Correct photogr. mats"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selection = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selection:
            obj.select = True
            for i in range(0,len(obj.material_slots)):
#                bpy.ops.object.material_slot_remove()
                obj.active_material_index = i
                ma = obj.active_material
                ma.specular_intensity = 0
                ma.alpha = 1.0
                ma.use_transparency = False
                ma.transparency_method = 'Z_TRANSPARENCY'
                ma.use_transparent_shadows = True
                ma.ambient = 0.0
                image = ma.texture_slots[0].texture.image
                image.use_alpha = False
        return {'FINISHED'}


class OBJECT_OT_IsometricScene(bpy.types.Operator):
    bl_idname = "isometric.scene"
    bl_label = "Isometric scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
#        bpy.context.scene.compression = 90
        bpy.context.scene.render.resolution_x = 3000
        bpy.context.scene.render.resolution_y = 3000
        bpy.context.scene.render.resolution_percentage = 100
        bpy.context.scene.game_settings.material_mode = 'GLSL'
        bpy.context.scene.game_settings.use_glsl_lights = False
        bpy.context.scene.world.light_settings.use_ambient_occlusion = True
        bpy.context.scene.render.alpha_mode = 'TRANSPARENT'
        return {'FINISHED'}


class OBJECT_OT_Canon6Dscene(bpy.types.Operator):
    bl_idname = "canon6d.scene"
    bl_label = "Canon 6D scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.context.scene.render.resolution_x = 5472
        bpy.context.scene.render.resolution_y = 3648
        bpy.context.scene.render.resolution_percentage = 100
        bpy.context.scene.tool_settings.image_paint.screen_grab_size[0] = 5472
        bpy.context.scene.tool_settings.image_paint.screen_grab_size[1] = 3648
        bpy.context.scene.game_settings.material_mode = 'GLSL'
        bpy.context.scene.game_settings.use_glsl_lights = False
        return {'FINISHED'}

class OBJECT_OT_Canon6D35(bpy.types.Operator):
    bl_idname = "canon6d35mm.camera"
    bl_label = "Set as Canon 6D 35mm"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selection = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selection:
            obj.select = True
            obj.data.lens = 35
            obj.data.sensor_fit = 'HORIZONTAL'
            obj.data.sensor_width = 35.8
            obj.data.sensor_height = 23.9
        return {'FINISHED'}

class OBJECT_OT_Canon6D24(bpy.types.Operator):
    bl_idname = "canon6d24mm.camera"
    bl_label = "Set as Canon 6D 14mm"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selection = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selection:
            obj.select = True
            obj.data.lens = 24
            obj.data.sensor_fit = 'HORIZONTAL'
            obj.data.sensor_width = 35.8
            obj.data.sensor_height = 23.9
        return {'FINISHED'}

class OBJECT_OT_Canon6D14(bpy.types.Operator):
    bl_idname = "canon6d14mm.camera"
    bl_label = "Set as Canon 6D 14mm"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selection = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selection:
            obj.select = True
            obj.data.lens = 14.46
            obj.data.sensor_fit = 'HORIZONTAL'
            obj.data.sensor_width = 35.8
            obj.data.sensor_height = 23.9
        return {'FINISHED'}

class OBJECT_OT_BetterCameras(bpy.types.Operator):
    bl_idname = "better.cameras"
    bl_label = "Better Cameras"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selection = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        for cam in selection:
            cam.select = True
            cam.data.show_limits = True
            cam.data.clip_start = 0.5
            cam.data.clip_end = 4
            cam.scale[0] = 0.1
            cam.scale[1] = 0.1
            cam.scale[2] = 0.1
        return {'FINISHED'}

class OBJECT_OT_NoBetterCameras(bpy.types.Operator):
    bl_idname = "nobetter.cameras"
    bl_label = "Disable Better Cameras"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selection = bpy.context.selected_objects
        bpy.ops.object.select_all(action='DESELECT')
        for cam in selection:
            cam.select = True
            cam.data.show_limits = False
        return {'FINISHED'}

#_______________________________________________________________________________________________________________

class CreateCameraImagePlane(bpy.types.Operator):
    """Create image plane for camera"""
    bl_idname= "object.createcameraimageplane"
    bl_label="Camera Image Plane"
    bl_options={'REGISTER', 'UNDO'}
    def SetupDriverVariables(self, driver, imageplane):
        camAngle = driver.variables.new()
        camAngle.name = 'camAngle'
        camAngle.type = 'SINGLE_PROP'
        camAngle.targets[0].id = imageplane.parent
        camAngle.targets[0].data_path="data.angle"

        depth = driver.variables.new()
        depth.name = 'depth'
        depth.type = 'TRANSFORMS'
        depth.targets[0].id = imageplane
        depth.targets[0].data_path = 'location'
        depth.targets[0].transform_type = 'LOC_Z'
        depth.targets[0].transform_space = 'LOCAL_SPACE'

    def SetupDriversForImagePlane(self, imageplane):
        driver = imageplane.driver_add('scale',1).driver
        driver.type = 'SCRIPTED'
        self.SetupDriverVariables( driver, imageplane)
        #driver.expression ="-depth*math.tan(camAngle/2)*resolution_y*pixel_y/(resolution_x*pixel_x)"
        driver.expression ="-depth*tan(camAngle/2)*bpy.context.scene.render.resolution_y * bpy.context.scene.render.pixel_aspect_y/(bpy.context.scene.render.resolution_x * bpy.context.scene.render.pixel_aspect_x)"
        driver = imageplane.driver_add('scale',0).driver
        driver.type= 'SCRIPTED'
        self.SetupDriverVariables( driver, imageplane)
        driver.expression ="-depth*tan(camAngle/2)"

    # get selected camera (might traverse children of selected object until a camera is found?)
    # for now just pick the active object

    def createImagePlaneForCamera(self, camera):
        imageplane = None
        try:
            depth = 10

            #create imageplane
            bpy.ops.mesh.primitive_plane_add()#radius = 0.5)
            imageplane = bpy.context.active_object
            imageplane.name = ("objplane_"+camera.name)
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=False)
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.transform.resize( value=(0.5,0.5,0.5))
            bpy.ops.uv.smart_project(angle_limit=66,island_margin=0, user_area_weight=0)
            bpy.ops.uv.select_all(action='TOGGLE')
            bpy.ops.transform.rotate(value=1.5708, axis=(0,0,1) )
            bpy.ops.object.editmode_toggle()

            imageplane.location = (0,0,-depth)
            imageplane.parent = camera

            #calculate scale
            #REPLACED WITH CREATING EXPRESSIONS
            self.SetupDriversForImagePlane(imageplane)

            #setup material
            if( len( imageplane.material_slots) == 0 ):
                bpy.ops.object.material_slot_add()
                #imageplane.material_slots.
            bpy.ops.material.new()
            mat_index = len(bpy.data.materials)-1
            imageplane.material_slots[0].material = bpy.data.materials[mat_index]
            material =  imageplane.material_slots[0].material
            # if not returned by new use imgeplane.material_slots[0].material
            material.name = 'mat_imageplane_'+camera.name

            material.use_nodes = False


            activename = bpy.path.clean_name(bpy.context.scene.objects.active.name)

            undistortedpath = bpy.context.scene.BL_undistorted_path

            if not undistortedpath:
                raise Exception("Hey Buddy, you have to set the undistorted images path !")

            bpy.context.object.data.uv_textures.active.data[0].image = bpy.data.images.load(undistortedpath+camera.name)

            bpy.ops.view3d.tex_to_material()

        except Exception as e:
            imageplane.select=False
            camera.select = True
            raise e
        return {'FINISHED'}

    def execute(self, context):
#        camera = bpy.context.active_object #bpy.data.objects['Camera']
        scene = context.scene
        undistortedpath = bpy.context.scene.BL_undistorted_path
        cam_ob = bpy.context.scene.camera

        if not undistortedpath:
            raise Exception("Set the Undistort path before to activate this command")
        else:
            obj_exists = False
            for obj in cam_ob.children:
                if obj.name.startswith("objplane_"):
                    obj.hide = False
                    obj_exists = True
                    bpy.ops.object.select_all(action='DESELECT')
                    scene.objects.active = obj
                    obj.select = True
                    return {'FINISHED'}
            if obj_exists is False:
                camera = bpy.context.scene.camera
                return self.createImagePlaneForCamera(camera)

class OBJECT_OT_paintcam(bpy.types.Operator):
    bl_idname = "paint.cam"
    bl_label = "Paint selected from current cam"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        scene = context.scene
        undistortedpath = bpy.context.scene.BL_undistorted_path
        cam_ob = bpy.context.scene.camera

        if not undistortedpath:
            raise Exception("Set the Undistort path before to activate this command")
        else:
            for obj in cam_ob.children:
                if obj.name.startswith("objplane_"):
                    obj.hide = True
            bpy.ops.paint.texture_paint_toggle()
            bpy.context.space_data.show_only_render = True
            bpy.ops.image.project_edit()
            obj_camera = bpy.context.scene.camera

            undistortedphoto = undistortedpath+obj_camera.name
            cleanpath = bpy.path.abspath(undistortedphoto)
            bpy.ops.image.external_edit(filepath=cleanpath)

            bpy.context.space_data.show_only_render = False
            bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}

class OBJECT_OT_applypaintcam(bpy.types.Operator):
    bl_idname = "applypaint.cam"
    bl_label = "Apply paint"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.paint.texture_paint_toggle()
        bpy.ops.image.project_apply()
        bpy.ops.paint.texture_paint_toggle()
        return {'FINISHED'}

