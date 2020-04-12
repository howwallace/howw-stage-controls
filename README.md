# howw-stage-controls

AUTHOR:		Harper O. W. Wallace  
DATE:		12 Apr 2020

#### DESCRIPTION OF STAGES SETUP:

This library executes move commands for Zaber Technologies rotary (1 x X-RSW60A) and linear (2 x T-LSM050A) stages, all using binary encoding, and it supervises voltage and current control of Keithley 2400 SourceMeter to open and close a Thorlabs SH05 beam shutter.

The two linear stages are mounted in the plane of the ground (one atop the other) and oriented orthogonally such that, from the perspective of the upper stage's platform, one stage controls the "x-coordinate of position," and the other controls the "y-coordinate." Film samples prepared on 1-inch microscope slides can be mounted on the upper stage using a 3D-printed slide-holder (slide_holder.stl) that I designed to be compatible with Zaber T-LSM050A stages.

The upper stage's platform has a range of motion such that the laser beam emitted from a 671nm, 450mW Laserglow laser module can strike any point in much of the central area of the upper platform, and therefore any point on a mounted film sample. The beam is projected horizontally above the stages, strikes a mirror and reflects vertically down, and is focused through a 10x microscope objective; it can be interrupted programmatically by means of a Thorlabs SH05 beam shutter (mounted between source and mirror), which is operated by modulating current from the Keithley 2400 SourceMeter (cf. keithley_handler.py). The 10x microscope objective is suspended in the beam path (vertically; after reflection) and above the film sample, in the optic holder of a modified student microscope whose coarse control is connected to the rotary stage to allow for programmatic control of the distance between lens and sample (corresponds to "z" in execute_commands.py).

"Writing" (used below and in .py files) entails moving a thin film of thermoresponsive materials (donor-acceptor columnar liquid crystals) on the stages beneath the focused beam to control their columnar alignment. For this particular application, particular considerations must be made to speed, power, and focal distance, but for the purposes of this overview, it is sufficient to say that the path that the beam follows corresponds to the pattern written to the sample.

___

#### execute_commands.py:

Parametrized move commands allow the user to write a single line, write parallel lines, write part of a circle, write a full circle, wipe a region, outline a region, and home all stages merely by specifying relevant parameters (e.g., circle center, radius, and write speed); many of these write functions are parametrized in several different ways in order to simplify writing slight variations on the same type of pattern (e.g., horizontal lines that span the entire sample region, v. vertical lines that span a specified sub-region, v. diagonal lines that are separated by a specified perpendicular distance). These commands and their arguments are detailed in execute_commands.py.

#### coordinates.py:

A Cartesian coordinate system keeps track of sample boundaries and write command positions within them. This system confers particular advantages in allowing the user to keep track of previously-written and new patterns in a systematic way, and also in conserving area on sample films in order to maximize their usefulness between wipes.

The coordinate system is defined by two critical parameters (1–2) and one very helpful one (3):
1. **GLOBAL_O** (*V2*) = "global origin," or the x- and y- stage positions when the laser beam is focused on the bottom-left corner of a square sample film
2. **TR** (*V2*) = "top right," etc.
3. **LOCAL_O** (*V2*) = "local origin," effectively a pointer vector from the origin, which allows the coordinate system to be sub-defined for a given write command, without needing to redefine GLOBAL_O or TR.

Although GLOBAL_O stands for "global origin," TR is actually another global origin and is often the more critical of the two to determine accurately, since it is ends up defining the apparent "bottom left" origin position relative to which moves are made, once the coordinate system is inverted to account for inversion on viewing under a microscope.

The user can define values for GLOBAL_O and TR using POSITION_GETTER_MODE (in execute_commands.py), which allows her to take manual control of the stages (using control knobs on the stages themselves) to adjust their position until they reach a desired position on the sample (e.g., GLOBAL_O or TR). At this point, the user can press the 'p' key on the keyboard to print the position of the stages to the console, so they may be recorded, e.g., to define GLOBAL_O and TR for a new sample (press 'esc' once these values have been recorded).

Units are millimeters, but neither class of Zaber stages uses this unit explicitly; instead, they use microsteps (which I call "data" in conversion methods, because those values are what ends up getting sent to the devices). Conversion factors between distance and speed are not intuitive, and they are different for the rotary and linear stages. Understanding how these units are interconverted is key to resolving issues where the stages do not behave as expected, which can happen. Consult [1] for a detailed explanation of Zaber's units and conversions.

This coordinate system will be more useful if it is specified for EACH film sample. To facilitate maintaining these boundary positions for different samples, I have designed (and installed, in our setup in Ebaugh Labs at Denison University) a 3D-printable 1-inch glass microscope slide holder that can be mounted to the Zaber T-LSM050A stage so that this coordinate system is approximately (~0.01mm) conserved on removal and replacement of the sample (cf. slide_holder.stl). Values for GLOBAL_O and TR should be stored in sample-specific .txt files (cf. samples/_example.txt), which are read by execute_commands.py 


#### mapping_handler.py

A new and experimental feature of this library is move mapping, which theoretically allows the user to simulate how write commands will turn out in order to correct any errors before running them on a sample; as a sort of extension of the coordinate system itself, this feature too is meant to help conserve space on the film and maximize usefulness between writes. Move mapping will be particularly advantageous for writing multi-step patterns that will be necessary to generate complex diffraction gratings for Fourier projection and holographic images. As I explain in more detail in the header of mapping_handler.py, rendering hasn't been rigorously tested yet; but it verifying predicted paths for different commands should be straightforward, and a procedure is outlined in the header of mapping_handler.py.

mapping_handler.py consults the .txt data file corresponding to the relevant film sample to gather historical write data and defined global origins. These film sample files must be made available for each sample (at the path specified in execute_commands.py), and in the format specified in samples/_example.txt and samples/_template.txt. Notes on how film sample files are used are offered in execute_commands.py, but here are some notes on syntax:
- Film sample files are interpreted in such a way that is compatible with the actual Python syntax for calling these commands. This allows the user to copy and paste commands between sample .txt files and the manual command-calling section of execute_commands.py (rather than having to reformat from some other input format). It makes using Move Mapping much more convenient (if only because you have to be familiar with only one command-calling syntax), but you should note that parsing out varied-type (e.g., int, float, V2, arrays) arguments from a string in a text file is nontrivial: it is critical that you use exactly the format that I describe in samples/_template.txt, and even so it is also possible that there are some text-parsing bugs that you will need to resolve.
- The interpreter will respect Python-syntax line comments (i.e., "# ..."), so I'd recommend commenting in information about laser power so you can keep track of it.
- Film sample data files use a special symbol ("## ...") to mark section divisions between already-written commands, new commands, and references; this symbol should not appear elsewhere than those three places (cf. samples/_template.txt).

Limitations of mapping_handler.py:
- If you want to modify a command method (e.g., write_line(...)), then you'll have to make sure that the corresponding section in mapping_handler.py is updated; if you want to add a new command method, then you'll need to define one in mapping_handler.py for it to be rendered.
- It assumes that your frame of reference for writing is based on the image on viewing under a microscope, which is an inversion of how patterns are actually written to the sample (i.e., assumes INVERT = True, cf. execute_commands.py). This means that if you change the value of INVERT in execute_commands.py, then the preview rendered by mapping_handler.py will be inverted.
- It hasn't been designed to shift shift historical information if you redefine a sample's GLOBAL_O or TR.

___

#### EXTREMELY IMPORTANT NOTES:
1. **DO NOT LET THE OBJECTIVE LENS HIT THE SAMPLE HOLDER SCREWS:**
Although it is possible to programmatically set a minimum height for the rotary stage to alleviate concerns like this, unfortunately the screws are sufficiently elevated above the sample that the focal distance would probably be too large to write at modest power, if you were to try that (rather than doing it that way, I have set the minimum position such that the aluminum jacket for the objective lens will not collide with the screws, so that the linear stages should not be damaged in a collision). Therefore it is EXTREMELY IMPORTANT that you move the stages such that the objective lens is someplace within the sample region, THEN lower the objective lens to the correct focal distance. This is done automatically in the parametrized move commands defined below, but if you define any more, or if you call move_to(...), then you must consider stage height.

2. **DO NOT MELT THE BEAM SHUTTER BY LEAVING THE LASER BEAM ON IT TOO LONG:**
If the laser spot is on the shutter leaves for too long, they will deform and the diaphragm will no longer be able to open and close. For the ThorLabs SH05 beam shutter we are using, about ten seconds is safe given the wavelength, spot size, and highest throughput of our laser (according to a ThorLabs Application Technician). This can be an inconvenience when you would like to move around the sample film without dragging an isotropic line behind you, e.g., and so it means that you may have to find creative ways to organize writing to minimize the time that the laser needs to be effectively "off"; alternatively, you may find that raising the objective lens sufficiently high will diffuse the beam such that you can move the sample without aligning/disaligning; as a last resort, you may need to TURN THE LASER OFF MANUALLY in certain circumstances, rather than relying on the beam shutter.

3. **DO NOT MOVE THE ROTARY STAGE AT TOO GREAT A SPEED OR ACCELERATION:**
Stage accelerations are defined in execute_commands.py (define_operating_constants), and I strongly recommend that you not alter them. The primary reason that you should not increase the rotary stage acceleration is that it'd be a huge problem if you bent or snapped the pin that runs through the coarse control of the microscope stage and which the rotary stage is rotating to control stage height; if this pin twists too abruptly (and I have no idea what the damage threshold is), you're probably going to need to build a new z-control stage and a new control adapter for the rotary stage, and you may do direct damage to the rotary stage and/or the object lens.
It's also important not to let the rotary stage move too fast: though it is possible with the linear stages, incorrect moves of the rotary stage are much more likely to cause actual damage (to the objective lens, to the sample, to the linear stages, and to itself). I've set an upper bound on speed so that the rotary stage moves slowly; this allows you to manually stop it (by pressing in once on the manual control knob) if it looks like it's heading for dangerous territory.

4. **YOU CAN INTERRUPT PROGRAMMED STAGE MOVES BY PRESSING SHIFT-CTRL-C**
I strongly recommend playing around with sending commands and interrupting them with Shift-Ctrl-C so you know. One notable quirk is that, if you interrupt writing a circle, the most recent move_vel command stands, and so one or both of the linear stages may just keep going until it is fully extended; obviously, this is a big concern if the tip of the objective lens is below the level of the sample holder screws.

5. **PUTTING A Nd MAGNET ARRAY DIRECTLY ON THE LINEAR STAGES INTERFERES WITH THEIR OPERATION**
They sort of spazzed out there, for a while. If you are interested in aligning in a strong B field, then make sure that you have the magnet array sufficiently far away from the stages (e.g., mounted above, with a several-inch spacer).


#### TROUBLESHOOTING:
- In Zaber Console, if pressing the "Stop" button does not update a stage's current position, it's probably because disable_auto_reply (used in binarydevice.py to selectively silence/allow responses) is still on. Still in Console, click on the device, then Settings, and reset "Device Mode" such that bit 0 = 0 (i.e., round down to the nearest even number).
- ModuleNotFoundError probably means that it has not been installed. Instructions for installing pip: https://pip.pypa.io/en/stable/installing/. Once it's installed, call: [sudo] pip install [the name of the module].
- You must multiple V2 objects by integers, rather than integers by V2 objects (cf. note in coordinates.py).
- If you turn the manual control knob on the rotary stage and it doesn't move, it's in Displacement Mode. To put it back in Velocity Mode, push in the control knob and hold it for a few seconds until the light blinks.
- If a serial connection cannot be made to the stages, make sure you've plugged in the USB to the port specified in execute_commands.py (define_operating_constants), or change the specified port to match where it's actually plugged in.


#### NOTES ON VERSION HISTORY
- Older versions of these Python libraries are available in this repo, but unfortunately they weren't saved as meaningful commits (i.e., I didn't use GitHub) but rather as ~random snapshots from when I got nervous about not having multiple copies. You may find it helpful to consult these versions to resolve issues, but note that I can't guarantee that the older versions were saved in fully functional states (e.g., maybe I was in the middle of adding new functionality when I saved them, I just can't remember, and now I can't test them).
- Control over Zaber stages alone is possible using old C# scripts (also available in this repo) that work with Zaber Console. Those files obviously have very different syntax, but more importantly they interact with Zaber stages quite differently; they may still be useful, though.


#### REFERENCE:
[1] https://www.zaber.com/protocol-manual?protocol=Binary
[2] https://www.zaber.com/support/docs/api/core-python/0.9/binary.html#binary-module
