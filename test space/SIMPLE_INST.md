blnder file
    make 2 collections "Main" and "Other"
    Main:add the target objects with its label name
    Other: add filler objects

Terminal code
    run: python arranger.py --blend-file ./Untitled.blend --output-dir ./output --image-count 5 --workers 2

File structure
    ./
        hdrs/
            <.hdr files here for diverse lighting>
        output/
        background_images/
            < add images (.jpg or something) with matching resolution>
        blenderfile.blend
        arranger.py
        render_and_label.py