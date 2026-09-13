# Step 11 Target Leakage Audit

The V2 target builder labels only events beginning strictly after T. Onset and false-onset labels were corrected: the existing V1 code included the current onset/surge day. Dry spell, severe break, heavy rain, revival, and horizon labels inspect only future rainfall after T.

The atmospheric source integration previously used backward fill for the first eight rows. V2 drops those boundary rows rather than allowing future atmospheric observations into training. All train/2024/test boundaries use a 37-day purge gap.

Current-state features such as rainfall, RH, dry streak, rolling rainfall, VPD, and hydrological memory are known at T and contain no future target-window observations.
