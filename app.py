import streamlit as st
import pandas as pd

st.set_page_config(page_title="Multi-BDN LNG Blender", layout="wide")

st.title("🚢 Multi-BDN LNG Composition Blender (Max 5)")
st.markdown("""
Select the exact number of Bunker Delivery Notes (up to 5) received during your bunkering operation. 
The application will dynamically generate the required inputs and calculate the combined weighted average.
""")

# --- STEP 1: INITIAL SELECTION ---
st.subheader("⚙️ Step 1: Define Bunkering Dimensions")
setup_col1, setup_col2 = st.columns(2)

with setup_col1:
    # Restricting to a user-defined selection up to a maximum of 5 BDNs
    num_bdns = st.number_input(
        "How many BDNs do you want to merge?", 
        min_value=2, 
        max_value=5, 
        value=2, 
        step=1,
        help="Supports processing for up to 5 distinct bunker delivery splits."
    )

with setup_col2:
    unit_basis = st.selectbox("Bunker Quantity Basis", ["Mass (MT)", "Liquid Volume (m³)"])

st.markdown("---")

# Pre-loaded exact constituents from your laboratory report spec
default_constituents = [
    ("Methane (CH4)", "mol%"),
    ("Ethane (C2H6)", "mol%"),
    ("Propane (C3H8)", "mol%"),
    ("iso-Butane (i-C4H10)", "mol%"),
    ("n-Butane (n-C4H10)", "mol%"),
    ("iso-Pentane (i-C5H12)", "mol%"),
    ("n-Pentane (n-C5H12)", "mol%"),
    ("n-Hexane (n-C6H14)", "mol%"),
    ("Nitrogen (N2)", "mol%"),
    ("Sulphur", "mg/m3")
]

# Baseline lab results to auto-populate BDN 1 for easy verification
bdn1_defaults = {
    "Methane (CH4)": 0.0000, "Ethane (C2H6)": 0.0000, "Propane (C3H8)": 0.0000,
    "iso-Butane (i-C4H10)": 0.0000, "n-Butane (n-C4H10)": 0.0000, "iso-Pentane (i-C5H12)": 0.0000,
    "n-Pentane (n-C5H12)": 0.0000, "n-Hexane (n-C6H14)": 0.0000, "Nitrogen (N2)": 0.0000,
    "Sulphur": 0.00
}

# --- STEP 2: DYNAMIC UI GENERATION FOR SELECTED BDNs ---
st.subheader(f"📋 Step 2: Enter Data for {num_bdns} BDNs")

# Dynamically generate exactly the number of columns selected by the user
bdn_cols = st.columns(num_bdns)
bdn_data = []

for i in range(num_bdns):
    with bdn_cols[i]:
        st.markdown(f"### 📄 BDN {i+1}")
        
        # Smart dynamic naming guides
        if i == 0:
            default_label = "Grey LNG"
        elif i == 1:
            default_label = "Bio-LNG"
        else:
            default_label = f"Bunker Stream {i+1}"
            
        bdn_name = st.text_input(f"Fuel Label", value=default_label, key=f"bdn_name_{i}")
        qty = st.number_input(f"Quantity ({unit_basis})", min_value=0.0, value=0.0,step=50.0, key=f"qty_{i}")
        
        st.markdown("**Composition Breakdowns**")
        comp = {}
        total_mol_pct = 0.0
        
        for g_name, g_unit in default_constituents:
            # Set smart defaults so the user doesn't have to fill all columns manually to test
            if i == 0 and g_name in bdn1_defaults:
                default_val = bdn1_defaults[g_name]
            elif i > 0 and g_name == "Methane (CH4)":
                default_val = 0.00 #if i == 1 else 95.00
            elif i > 0 and g_name == "Nitrogen (N2)":
                default_val = 0.00 #if i == 1 else 5.00
            else:
                default_val = 0.00
                
            val = st.number_input(
                f"{g_name} ({g_unit})", 
                min_value=0.0, 
                max_value=1000.0, 
                value=default_val, 
                step=0.0001, 
                format="%.4f", 
                key=f"g_val_{g_name}_{i}"
            )
            comp[g_name] = val
            
            if g_unit == "mol%":
                total_mol_pct += val
                
        # Independent column validation
        # Independent column validation
        if total_mol_pct < 99.99 or total_mol_pct > 100.01:
            st.error(f"⚠️ Total: {total_mol_pct:.4f}% (Must be 100%)")
            is_valid = False
        else:
            st.success(f"✅ Total: {total_mol_pct:.4f}%")
            is_valid = True
            
        bdn_data.append({
            "name": bdn_name,
            "quantity": qty,
            "composition": comp,
            "valid": is_valid
        })

st.markdown("---")

# --- STEP 3: BLENDING CALCULATIONS & DISPLAYS ---
st.subheader("📊 Step 3: Combined Blended Manifest")

all_valid = all([b["valid"] for b in bdn_data])
total_quantity = sum([b["quantity"] for b in bdn_data])

if total_quantity == 0:
    st.warning("Please assign quantities greater than zero to evaluate the blend matrix.")
elif not all_valid:
    st.error("Processing blocked. Please verify that all individual 'mol%' columns sum up to exactly 100.00%.")
else:
    # Compute the final weighted blend across the dynamically built array
    final_blend = {}
    total_final_mol_pct = 0.0

    # FIXED: Correctly unpack both the constituent name and its corresponding unit
    for g_name, g_unit in default_constituents:
        weighted_sum = sum([bdn["quantity"] * bdn["composition"][g_name] for bdn in bdn_data])
        final_blend[g_name] = weighted_sum / total_quantity

        # Track the total of the final blended mol% components
        if g_unit == "mol%":
            total_final_mol_pct += final_blend[g_name]

    # Display structures side-by-side
    res_col1, res_col2 = st.columns([2, 1])
    
    with res_col1:
        # Build dynamic DataFrame columns
        df_dict = {
            "Constituent": [g[0] for g in default_constituents],
            "Unit": [g[1] for g in default_constituents]
        }
        
        for bdn in bdn_data:
            df_dict[bdn["name"]] = [bdn["composition"][g[0]] for g in default_constituents]
            
        df_dict["FINAL COMBINED BLEND"] = [round(final_blend[g[0]], 4) for g in default_constituents]
        
        df = pd.DataFrame(df_dict)
        st.dataframe(df.set_index("Constituent"), use_container_width=True)

    with res_col2:
        st.metric(label=f"Total Combined Quantity ({unit_basis})", value=f"{total_quantity:,.2f}")

        # Visual confirmation that the math balances out perfectly (adjusted tolerance to match 4 decimal precision)
        if total_final_mol_pct < 99.99 or total_final_mol_pct > 100.00:
            st.error(
                f"⚠️ Blended Total: {total_final_mol_pct:.4f}%.\n\n"
                "Adjust it 100% before using the blended profile in calculations."
            )
        else:
            st.success(f"✅ Blended Total: {total_final_mol_pct:.2f}%")
        
        methane_label = default_constituents[0][0]
        st.metric(label=f"Blended {methane_label} Profile", value=f"{final_blend[methane_label]:.4f} mol%")
        
        # Download report engine
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Combined BDN Report (CSV)",
            data=csv,
            file_name="multi_bdn_lng_blend_report.csv",
            mime="text/csv",
        )