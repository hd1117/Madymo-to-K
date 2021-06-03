"""
Harry Duckworth
Dyson School of Design Engineering
Imperial College London

Ready a madymo linear and rotational acceleration file and export it as a k file for LS-DYNA
"""
import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def read_madymo(source):
    """
    Open Madymo file and import it to dataframe
    """

    # Initilise variables
    line_counter = 1
    object_counter = 1
    choices = []
    acc_data = []
    time_data = []
    picked_choice = False
    not_valid = True
    columns = []
    component_matches = ["m/s**2", "rad/s**2"]

    # Open Madymo File     
    with open(source) as m:
        
        # Loop through all lines in file
        for line in m:

            # Update line counter
            line_counter += 1

            # Generate split line
            line_split = line.split()

            # Skip first three lines
            if line_counter < 5:
                continue

            # Import acc data 
            elif (len(line_split) == 4) and ('E+' in line):

                # Import if the chosen line 
                if object_counter == chosen_object:

                    acc_data.append([
                            float(line_split[1]),
                            float(line_split[2]), 
                            float(line_split[3])
                            ])

                object_counter += 1
 
            # Import time 
            elif len(line_split) == 1 and not('(' in line):
                time_data.append(float(line.strip()))

                # Reset object counter 
                object_counter = 1

            # Get components choices:
            elif any(x in line for x in component_matches):
                columns.append(line.strip())

                # display object choices and pick
                if not picked_choice:
                    n = 1
                    for i in choices:

                        print('[' + str(n) + ']      ' + i)
                        n += 1
                    
                    # Get user input
                    while not_valid:
                        chosen_object = input('Which object do you want to export acceleration for: ')
                        
                        # Check is int format
                        try:
                            chosen_object = int(chosen_object)
                            
                            # Check input is wiwthing valid range
                            if all([chosen_object <= n, chosen_object >= 0]):
                                
                                # Allow code to progress if valid
                                not_valid = False
                                picked_choice = True

                            # Error Message
                            else:
                                print('Please enter a valid number')
                        
                        # Error Message
                        except:
                            print('Please enter a valid number')
            else:
                choices.append(line)
 
    df_acc = pd.DataFrame(acc_data, columns = columns[1:4], index = time_data)

    print('\nCheck Data being imported: ')
    print(df_acc.head())
    print()

    return df_acc

def write_acc_comp(curve, cog_id, pres_motion_dof, pres_motion_type, lcid, output_acc_file):
    '''
    Create a k file for acceleration curve
    '''
 
    # Write prescribed motion keyword (this applies the curve to the centre of gravity)
    output_acc_file.write("*BOUNDARY_PRESCRIBED_MOTION_RIGID\n")
    output_acc_file.write("$#     pid       dof       vad      lcid        sf       vid     death     birth\n")
    output_acc_file.write(str(cog_id).rjust(10) +
                            str(pres_motion_dof).rjust(10) +
                            str(pres_motion_type).rjust(10) +
                            str(lcid).rjust(10) +
                            "       1.0         01.00000E28       0.0\n")
    output_acc_file.write("*DEFINE_CURVE_TITLE\n")
    output_acc_file.write("Acceleration component\n")
    output_acc_file.write("$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint\n")
    output_acc_file.write(str(lcid).rjust(10)+"         0       1.0       1.0       0.0       0.0         0         0\n")
    output_acc_file.write("$#                a1                  o1  \n")

    # Get time and data
    time = curve.index.values.tolist()
    data = curve.iloc[:].tolist()

    # Loop through each timestep and print  
    for i in range(len(time)):
        output_acc_file.write(str(round(time[i],10)).rjust(20) + str(round(data[i],10)).rjust(20) + '\n') 

def plot_acc(df_lin, df_rot):
    """
    Create plots of acc data
    """

    sns.set_theme()
    sns.set_style("ticks")
    sns.set_context("paper")

    n = 1
    fig, ax = plt.subplots(2, sharex=True, figsize = (5, 5))
    labels = ['x', 'y', 'z', 'x', 'y', 'z']
    start_times = [0, 0, 0]
    end_times = [0, 0, 0]
    colors = ['forestgreen', 'steelblue', 'darkorchid', 'firebrick', 'darkorange', 'gold']

    sns.lineplot(
        ax=ax[0], 
        data=df_lin, 
        palette=colors[0:3], 
        linewidth=1,
        dashes=False
        )

    sns.lineplot(
        ax=ax[1], 
        data=df_rot, 
        palette=colors[3:6], 
        linewidth=1,
        dashes=False
        )

    ax[0].set_ylabel('Linear Acceleration $(m/s^2)$')
    ax[1].set_ylabel('Rotational Velocity $(rad/s)$')
    ax[1].set_xlabel('Time $(ms)$')

    plt.savefig('acc.svg', bbox_inches='tight', dpi = 600)
    plt.savefig('acc.png', bbox_inches='tight', dpi = 600)

    plt.show()

def create_acc_file(df_lin, df_rot, cog_id):

    max_time = min(df_lin.index[-1], df_rot.index[-1])

    # Create file
    output_acc_file = open(os.path.join("acceleration" + ".k"), "w+")
    n = 0
        
    output_acc_file.write("*CONTROL_TERMINATION\n")
    output_acc_file.write("$#  endtim    endcyc     dtmin    endeng    endmas     nosol  \n")
    output_acc_file.write(str(round(max_time, 9)).rjust(10) + "         0       0.0       0.01.000000E8         0\n")

    print("Writing acceleration data...")
    
    # Variables
    pres_motion_dof  = 1
    lcid = 1

    # Constants
    pres_motion_type_lin = 1
    pres_motion_type_rot = 0

    for col in df_lin.columns:
        write_acc_comp(df_lin[col], cog_id, pres_motion_dof, pres_motion_type_lin, lcid, output_acc_file)
        
        # Update Variabels
        pres_motion_dof += 1 
        lcid += 1
        
    pres_motion_dof += 1 

    for col in df_rot.columns:
        write_acc_comp(df_rot[col], cog_id, pres_motion_dof, pres_motion_type_lin, lcid, output_acc_file)
        
        # Update Variabels
        pres_motion_dof += 1 
        lcid += 1
        
    output_acc_file.write("*END\n")
    output_acc_file.close()

if __name__ == "__main__":

    # System arguments
    madymo_lin_acc_file = sys.argv[1]
    madymo_rot_acc_file = sys.argv[2]
    cog_id = sys.argv[3]

    # User Messages
    print("Creating acceleration file using: ")
    print('    ' + madymo_lin_acc_file)
    print('    ' + madymo_rot_acc_file)

    # Import Data to Dataframes
    df_lin = read_madymo(madymo_lin_acc_file)
    df_rot = read_madymo(madymo_rot_acc_file)

    # Create Plots 
    plot_acc(df_lin, df_rot)

    # Scale data to mm and ms
    df_lin = df_lin.multiply(1/1000)
    df_rot = df_rot.multiply(1/1000000)

    # Create k file
    create_acc_file(df_lin, df_rot, cog_id)
