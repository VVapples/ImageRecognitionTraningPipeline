now i want you to make a set of .py files that work together which will work together to generate tons of images using the blender rendering system.
when rendering, i want you to keep in mind that these will be used to train a yolo model so i want you to make sure to label the object before closing or rearranging again for repeating.

the input and the sequence will be the following

arranger:
     - Discription: recieves input and activates multiple instances of setupper/renderer to start the image generatation
     - Input: image count, parallel worker count, output folder, input folder(.blend file)
|
V
setupper/renderer:
     - Discription: opens blendfile, rearranges the scene(see refrence 1) and renders the image and saves it to the designated file, at the same time it'll make a label for a yolo image recognition model(see refrence 2).

refrence
1. steps are in attatched scene_preparer.py, use this as an example to do the rearranging.
2. in the .blend file there should be 2 collections, one is called "Main" and the other is called "Other", main is the image training target so label all the objects in there separately with their name.(if the object is called "orange" the label class will be "orange") for the objects in "Other", just ignore them. they are just filler objects.
3. for the rendering settings, follow what is setup in the .blend file


```bash
python arranger.py --blend-file ./Untitled.blend --output-dir ./output --image-count 5 --workers 2
```