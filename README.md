# howw-stage-controls
 

REFERENCE:
https://www.zaber.com/support/docs/api/core-python/0.9/binary.html#binary-module


TROUBLESHOOTING:
 - IF (IN CONSOLE) PRESSING STOP DOES NOT DISPLAY THE CURRENT POSITION, I THINK IT'S
   PROBABLY BECAUSE DISABLE_AUTO_REPLY IS ON.  RESET DEVICE MODE SUCH THAT BIT 0 = 0.
 - ModuleNotFoundError probably means that it hasn't been installed.
	Instructions for installing pip:  https://pip.pypa.io/en/stable/installing/
	[sudo] pip install ...