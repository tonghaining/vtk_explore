import vtk

def get_program_parameters():
    import argparse
    description = 'Read a VTK image data file.'
    epilogue = ''''''
    parser = argparse.ArgumentParser(description=description, epilog=epilogue,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('filename', help='shoulder.vti')
    args = parser.parse_args()
    return args.filename

def main():
    file_name = get_program_parameters()
    arender = vtk.vtkRenderer()
    arender.SetViewport(0, 0.0, 0.5, 1.0)
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(arender)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)
    imr = vtk.vtkXMLImageDataReader()
    imr.SetFileName(file_name)
    imr.Update()

    # extract bone🦴, and polish a bit😈
    bone_extractor = vtk.vtkContourFilter()
    bone_extractor.SetInputConnection(imr.GetOutputPort())
    bone_extractor.SetValue(0, 1500)
    bone_extractor.ComputeGradientsOn();
    bone_extractor.ComputeScalarsOn();
    smooth = vtk.vtkSmoothPolyDataFilter()
    smooth.SetInputConnection(bone_extractor.GetOutputPort())
    smooth.SetNumberOfIterations(100)

    # 面模型切割
    bone_normals = vtk.vtkPolyDataNormals()
    bone_normals.SetInputConnection(smooth.GetOutputPort())
    bone_normals.SetFeatureAngle(50)

    bone_stripper = vtk.vtkStripper()
    bone_stripper.SetInputConnection(bone_normals.GetOutputPort())
    #----------

    bone_mapper = vtk.vtkPolyDataMapper()
    bone_mapper.SetInputConnection(bone_stripper.GetOutputPort())
    bone_mapper.ScalarVisibilityOff()

    bone = vtk.vtkActor()
    bone.SetMapper(bone_mapper)

    # outline
    outlineData = vtk.vtkOutlineFilter()
    outlineData.SetInputConnection(imr.GetOutputPort())

    mapOutline = vtk.vtkPolyDataMapper()
    mapOutline.SetInputConnection(outlineData.GetOutputPort())

    outline = vtk.vtkActor()
    outline.SetMapper(mapOutline)
    outline.GetProperty().SetColor(0, 0, 0)

    camera = vtk.vtkCamera()
    camera.SetViewUp(0, 0, -1)
    camera.SetPosition(0, 1, 0)
    camera.ComputeViewPlaneNormal()
    camera.Azimuth(30.0)
    camera.Elevation(30.0)
    camera.Dolly(1.5)

    arender.AddActor(outline)
    arender.AddActor(bone)
    arender.SetActiveCamera(camera)
    arender.ResetCamera()
    arender.SetBackground(.2, .3, .4)
    arender.ResetCameraClippingRange()

    transform = vtk.vtkTransform()
    transform.Translate(1.0, 0.0, 0.0)
    # axes🧭
    axes = vtk.vtkAxesActor()
    axes.SetUserTransform(transform)
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(renWin)
    widget = vtk.vtkOrientationMarkerWidget()
    widget.SetOrientationMarker(axes)
    widget.SetInteractor(interactor)
    widget.SetEnabled(1)
    widget.InteractiveOn()
    interactor.Initialize()

    renWin.SetSize(1000, 1000)
    style = vtk.vtkInteractorStyleTrackballCamera()
    iren.SetInteractorStyle(style);
    # cliper：https://vtk.org/doc/nightly/html/classvtkClipPolyData.html
    global cliper
    cliper = vtk.vtkClipPolyData()
    cliper.SetInputData(bone_stripper.GetOutput())
    # define implicit plane
    implicit_plane_widget = vtk.vtkImplicitPlaneWidget()
    implicit_plane_widget.SetInteractor(iren)
    implicit_plane_widget.SetPlaceFactor(1.25)
    implicit_plane_widget.SetInputData(bone_stripper.GetOutput())
    implicit_plane_widget.PlaceWidget()
    implicit_plane_widget.OriginTranslationOn ()
    # cone
    global cone_bone_actor
    cone_bone_actor = vtk.vtkActor()
    cone_bone_actor.SetMapper(bone_mapper)
    # display the plane
    rRenderer = vtk.vtkRenderer()
    rRenderer.SetBackground(0.2, 0.3, 0.5)
    rRenderer.SetViewport(0.5, 0.0, 1.0, 1.0)

    cone_bone_actor.RotateZ(90)
    rRenderer.AddActor(cone_bone_actor)

    renWin.AddRenderer(rRenderer)
    # add call back function
    implicit_plane_widget.AddObserver("EndInteractionEvent", my_call_back)
    implicit_plane_widget.On()

    renWin.Render()
    iren.Initialize()
    iren.Start()

def my_call_back(pWidget,ev):
# invoked when pWidget changed
    if (pWidget):
        print(pWidget.GetClassName(), "Event Id:", ev)
        planeNew = vtk.vtkPlane()
        pWidget.GetPlane(planeNew)
        cliper.SetClipFunction(planeNew)
        # get plane of pWidget
        planeNew.GetNormal()
        cliper.Update();
        # send cliped model to the other window
        clipedData = vtk.vtkPolyData()
        clipedData.DeepCopy(cliper.GetOutput())

        coneMapper = vtk.vtkPolyDataMapper()
        coneMapper.SetInputData(clipedData)
        coneMapper.ScalarVisibilityOff()
        cone_bone_actor.SetMapper(coneMapper)
        print("Plane Normal = "+str(planeNew.GetNormal()))
        print("Plane Origin = "+str(planeNew.GetOrigin()))
        
if __name__ == '__main__':
    main()