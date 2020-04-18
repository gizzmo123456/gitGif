import os, sys, subprocess
import imageio
from skimage import transform

# theses need to be nested in "[command]"
git_get_tracked_files = ' git ls-tree -r master --name-only '
git_get_commits = ' git log --follow -- '   # requires the file name to be appended to the end
git_get_current_branch = 'git rev-parse --abbrev-ref HEAD'

supported_files = ["jpg", "png"]

current_branch = None           # this is so we can return to this branch once we have collected our images
tracked_files = []
selected_file_id = -1
selected_file_commits = []
images = []

duration = 0
output_scale = -1


def return_to_current_branch():

    git_checkout = 'git checkout ' + current_branch[ :-1 ]
    print( git_checkout )

    for line in process( git_checkout ):
        print( line )


def process_input(ty, message, while_func_eval, start_val=-1):

    while while_func_eval(start_val):
        try:
            start_val = ty( input( message ) )
        except:
            pass

    return start_val


def process(git_command):

    proc = subprocess.Popen( [ 'python', '-c', 'import os;os.system( "' + git_command + '" )' ], stdout=subprocess.PIPE )

    while True:
        line = proc.stdout.readline().decode( "utf-8" )
        if not line:
            break
        else:
            yield line

    proc.kill()


# get our current branch
proc = subprocess.Popen(['python', '-c', 'import os;os.system( "'+ git_get_current_branch +'" )'], stdout=subprocess.PIPE)
line = proc.stdout.readline().decode( "utf-8" )
if line:
    current_branch = line

print( "current branch: ", current_branch )

# get all all tracked files for the master branch
for line in process(git_get_tracked_files):
    line = line.replace("\n", "")
    if line.split(".")[-1] in supported_files:
        tracked_files.append( line )
        print("["+ str(len(tracked_files) - 1) +"] -", line)

# let user select a file, set the duration and output scale
selected_file_id = process_input(int, "Enter file [id]\n", lambda v: v < 0 or v > len( tracked_files ))
duration = process_input(float, "Enter frame duration (seconds)(or < 0 to exit)(max 10)\n",
                         lambda v: v == 0 or v > 10, start_val=0 )

if duration < 0:
    exit()

output_scale = process_input(float, "image scale (max 5)\n", lambda v: v <= 0 or v > 5)

# get the commits for the selected file
for line in process(git_get_commits + tracked_files[ selected_file_id ]):
    line = line.split(" ")
    if line[0] == "commit":
        commit = line[1].replace( "\n", "" )
        selected_file_commits.append( commit )
        print(commit)

# now we have all the commits we can checkout to each one and get a copy of that image
for c in selected_file_commits:
    # checkout to the commit
    git_checkout = 'git checkout --detach '+c
    print( git_checkout )

    for line in process( git_checkout ):
        print(line)

    try:
        img = imageio.imread( tracked_files[ selected_file_id ] )
        x, y, d = img.shape
    except Exception as e:
        print(e)
        print("Skipping as a result.")
        continue

    try:
        if output_scale != 1:
            img = transform.resize( img, (x * output_scale, y * output_scale), mode='symmetric', preserve_range=True )
    except Exception as e:
        print( e )
        print( "Unable to resize image, using default!" )

    images.append( img )

# lets not forget to checkout back to our start branch
return_to_current_branch()

# compile our image into a gif :)
print("Saving Gif!")

file_name = tracked_files[ selected_file_id ].split(".")[0]
try:
    with imageio.get_writer( str(file_name)+'.gif', mode='I', duration=duration ) as write:
        for img in reversed(images):
            write.append_data(img)
    print( "Successful :D" )
except Exception as e:
    print("Failed!\n", e)
