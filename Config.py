import sys

try:
    command = sys.argv[1]
        
except IndexError:
    print("\nUsage "+sys.argv[0]+" <start|stop>\n")
    exit(1)

try:

    URL=''
    WDIR='./'
    PILING_NAME=URL.split('/')[2]
    PILING_DB=WDIR+PILING_NAME+'.sqlite'
    PILING_LOG=WDIR+PILING_NAME+'.log'

except IndexError:
    print("Wrong configuration. Edit Config.py. Exiting.", file=sys.stderr)
    exit(2)
