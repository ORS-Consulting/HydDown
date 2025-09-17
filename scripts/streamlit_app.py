# HydDown     hydrogen/other gas depressurisation
# Copyright (c) 2021 Anders Andreasen
# Published under an MIT license

import streamlit as st
import pandas as pd
from PIL import Image
import base64
import matplotlib.pyplot as plt
import sys
import os

try:
    from hyddown import HydDown
except:
    
    hyddown_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "src")
    sys.path.append(os.path.abspath(hyddown_path))
    from hyddown import HydDown


def get_table_download_link(df, filename):
    """
    Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(
        csv.encode()
    ).decode()  # some strings <-> bytes conversions necessary here
    filename = filename + ".csv"
    return f'<a href="data:application/octet-stream;base64,{b64}" download={filename}>Download csv file</a>'


def read_input():
    sideb = st.sidebar

    with sideb:
        image_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "..",
            "docs",
            "img",
            "ORS_logo_JPEG.jpg",
        )
        st.markdown(
            """<a href="https://www.ors-consulting.com">
            <img src="data:image/png;base64,{}" width="100">
            </a>""".format(
                base64.b64encode(open(image_path, "rb").read()).decode()
            ),
            unsafe_allow_html=True,
        )
        st.write("")
        #icon = Image.open(image_path)
        #st.image(icon, width=100, caption="ORS Consulting HydDown App")
        #st.logo(icon, size="large", link="http://www.ors-consulting.com", icon_image=None)

        image_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "..",
            "docs",
            "img",
            "Sketch.png",
        )
        icon = Image.open(image_path)
        st.image(icon, use_container_width=True, caption="HydDown")
        
       
        heattran = st.checkbox("Include heat transfer", value=True)
        c1, c2 = st.columns(2)

        with c2:
            length = st.text_input("Vessel length (m):", 0.463)
            diam = st.text_input("Vessel diam (m):", 0.254)
            thk = st.text_input("Vessel thickness (m):", 0.016)
            orientation = st.selectbox(
                "Vessel orientation", ("horizontal", "vertical")
            )
            orifice_diam = st.text_input("Orifice diam (mm):", 0.40)
            orifice_diam = float(orifice_diam) / 1000
            tstep = st.text_input("Time step (s):", 1.0)

        with c1:
            pres = st.text_input("Initial pressure (bar):", 50.0)
            pres = float(pres) * 1e5

            back_pressure = st.text_input("Fill/back pres. (bar):", 240)
            back_pressure = float(back_pressure) * 1e5

            #fluid = st.selectbox('Select fluid', ('H2', 'He', 'N2', 'air', 'CH4', 'O2'))
            fluid = st.selectbox('Select fluid', ('H2', 'NG', 'NG1', 'He', 'N2', 'air', 'CH4','O2'))
            if fluid == 'NG':
                fluid = "Methane[0.89571]&Ethane[5.6739e-02]&Propane[2.30395e-02]&Butane[1.03E-02]&Pentane[2.67E-03]&CO2[0.84e-02]&N2[0.3080e-2]"
            if fluid == 'NG1':
                fluid = "Methane[0.860231]&Ethane[0.078217]&Propane[0.033786]&Butane[9.210E-03]&Pentane[2.573E-03]&Hexane[3.560E-04]&CO2[1.206E-02]&N2[3.701E-03]"

            mode = st.selectbox('Select mode', ('filling', 'discharge'))
            temp = st.text_input("Initial temp. (C):", 25)
            temp = float(temp) + 273.15
            end_time = st.text_input("End time (s):", 240)

        density = st.text_input("Vessel material density (kg/m3):", 7740)
        density = float(density)

        cp = st.text_input("Vessel material heat capacity (J/kg K):", 470)
        cp = float(cp)

    input = {}
    input["calculation"] = {}
    input["vessel"] = {}
    input["initial"] = {}
    input["valve"] = {}
    input["heat_transfer"] = {}

    input["calculation"]["type"] = "energybalance"
    input["calculation"]["time_step"] = float(tstep)
    input["calculation"]["end_time"] = float(end_time)

    input["vessel"]["length"] = float(length)
    input["vessel"]["diameter"] = float(diam)
    input["vessel"]["heat_capacity"] = cp
    input["vessel"]["density"] = density
    input["vessel"]["orientation"] = orientation
    input["vessel"]["thickness"] = float(thk)

    input["initial"]["pressure"] = pres
    input["initial"]["temperature"] = temp
    input["initial"]["fluid"] = fluid
    input["valve"]["flow"] = mode
    input["valve"]["type"] = "orifice"
    input["valve"]["diameter"] = float(orifice_diam)
    input["valve"]["discharge_coef"] = 0.84
    input["valve"]["back_pressure"] = back_pressure
    # input['valve']['end_pressure']=end_pressure

    input["heat_transfer"]["type"] = "specified_h"
    input["heat_transfer"]["temp_ambient"] = 298
    input["heat_transfer"]["h_outer"] = 5
    if heattran is True:
        input["heat_transfer"]["h_inner"] = "calc"
    else:
        input["heat_transfer"]["h_inner"] = 0.0
    input["heat_transfer"]["D_throat"] = float(diam)
    return input


if __name__ == "__main__":
    st.set_page_config(layout="wide")

    input = read_input()
    hdown = HydDown(input)
    st.title("HydDown rigorous demo")

    if st.sidebar.button("Run Simulation", type="primary"):
        with st.spinner("Calculating, please wait...."):
            hdown.run(disable_pbar=True)
        
        
    
            df = hdown.get_dataframe()
            file_name = st.text_input("Filename for saving data:", "saved_data")
        
            st.markdown(get_table_download_link(df, file_name), unsafe_allow_html=True)
        
            col1, col2 = st.columns(2)
        
            if input["valve"]["flow"] == "discharge":
                temp_data = pd.DataFrame(
                    {
                        "Time (s)": hdown.time_array,
                        "Fluid temperature (C)": hdown.T_fluid - 273.15,
                        "Wall temperature (C)": hdown.T_vessel - 273.15,
                        "Vent temperature (C)": hdown.T_vent - 273.15,
                    }
                )
            else:
                temp_data = pd.DataFrame(
                    {
                        "Time (s)": hdown.time_array,
                        "Fluid temperature (C)": hdown.T_fluid - 273.15,
                        "Wall temperature (C)": hdown.T_vessel - 273.15,
                    }
                )
        
            pres_data = pd.DataFrame(
                {"Time (s)": hdown.time_array, "Pressure (bar)": hdown.P / 1e5}
            )
        
            fig, ax = plt.subplots(figsize=(5, 2))
        
            ax.plot(
                pres_data["Time (s)"],
                pres_data["Pressure (bar)"],
                "k",
            )
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Pressure (bar)")
            col1.pyplot(fig)
        
            fig, ax = plt.subplots(figsize=(5, 2))
        
            ax.plot(
                temp_data["Time (s)"], temp_data["Fluid temperature (C)"], "k", label="Fluid"
            )
            ax.plot(
                temp_data["Time (s)"], temp_data["Wall temperature (C)"], "k--", label="Wall"
            )
            if input["valve"]["flow"] == "discharge":
                ax.plot(
                    temp_data["Time (s)"],
                    temp_data["Vent temperature (C)"],
                    "k-.",
                    label="Vent",
                )
        
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Temperature ($^\circ$C)")
            ax.legend(loc="best")
            col2.pyplot(fig)
        
            mdot_data = pd.DataFrame(
                {"Time (s)": hdown.time_array, "Mass rate (kg/s)": hdown.mass_rate}
            )
            mass_data = pd.DataFrame(
                {"Time (s)": hdown.time_array, "Fluid inventory (kg)": hdown.mass_fluid}
            )
        
            fig, ax = plt.subplots(figsize=(5, 2))
            ax.plot(
                mdot_data["Time (s)"],
                mdot_data["Mass rate (kg/s)"],
                "k",
            )
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Mass rate (kg/s)")
            col1.pyplot(fig)
        
            fig, ax = plt.subplots(figsize=(5, 2))
            ax.plot(
                mass_data["Time (s)"],
                mass_data["Fluid inventory (kg)"],
                "k",
            )
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Fluid inventory (kg)")
            col2.pyplot(fig)
    else:
        st.info(
            "👈 Configure parameters in the sidebar and click 'Run Simulation' to start the analysis."
        )

        st.markdown(
            """
        ## About This Simulation
        
        This application simulates the depressurisation or filling of a vessel with gas. It was initially developed for hydrogen
        but can be used for any single component gas and non-condensing gasseous mixtures. The thermal response of the fluid as
        well as vessel wall is rigorously modelled. 
        
        **Key Features:**
        - **Real gas** vessel pressurisation/depressurisation with heat transfer from gas to vessel and ambient and vice versa. 
        - Default Orifice discharge coefficient (Cd = 0.84) is specified for desired pressurisation/depressurisation rate.
        - **Dynamic simulation**: Models the time-dependent pressure and temperature development in fluid and vessel wall
        - **First law flow process**: Heat and mass balances solved concurrently 
        - **Heat transfer calculation**: Heat transfer between vessel wall and fluid using both natural and forced convection
        - **Wall heat transfer**: Thermal gradients are assumed negligible in the wall (Type I cylinder). 
        - **Accurate thermodynamics**: Utilizes [CoolProp](https://coolprop.org/) for equation of state and property calculations
        - **Complete data export**: Download all simulation data in a csv file

        **Key questions answered**
        - What is the required time for depressurisation/pressurisation? 
        - What is the minimum/maximum temperature of the vessel wall during filling/discharge?
        - What is the temperature of the gas vented during depressurisation?
        
        **Further information**
        - Code available on [**github**](https://github.com/ORS-consulting/HydDown)
        - [**Manual**](https://github.com/ORS-Consulting/HydDown/raw/main/docs/MANUAL.pdf) available
        - Extensive **validation** documented in the [manual](https://github.com/ORS-Consulting/HydDown/raw/main/docs/MANUAL.pdf)
        - **Paper published** in [Journal of Open Source Software](https://doi.org/10.21105/joss.03695)
        - The full program can also manage **1-D heat transfer in dual composites**, external **fire heat load**, different vessel geometries. 

        **Tips and tricks**
        - Eventually you may experience an error. This is typically due to a combination of a too large time step relative to a too high mass rate. Either decrease the time step and/or the orifice size.
        - Check the results with a lower time step to see if the results change. If not - you're good to go, otherwise decrease the time step until the results are independent of the time step.
        - Remember: For discharge simulation, the initial pressure must exceed the back pressure, and vice versa for filling the initial pressure shall be lower than the fill pressure.

        **Disclaimer**
        This app and the underlying code is provided free of charge under a BSD license. 
        
        """
        )
