import numpy as np
from astropy.coordinates import SkyCoord, SkyOffsetFrame
import astropy.units as u
import pandas as pd
import argparse
import sys

class PlatoPoint:
    def __init__(self):
        # 1. Define Payload Center
        self.payload_center = SkyCoord(l=255.9425 * u.deg, 
                                       b=-24.63082 * u.deg, 
                                       frame='galactic')
        
        # 2. Define the "Master" Payload Frame
        # This acts as the flat focal plane of the spacecraft.
        # All "Parallel" definitions are relative to this frame.
        self.payload_frame = SkyOffsetFrame(origin=self.payload_center)
        
        # 3. Geometry Constants - these have been iterated to best match the official results (97%)
        self.camera_azimuths = [45, 135, 225, 315] * u.deg
        self.camera_offset_dist = 9.193 * u.deg
        self.circle_radius = 38.393/2 * u.deg
        self.square_half_width = 17.705 * u.deg 
        self.gap_half_width = (18.5 * u.arcmin).to(u.deg) / 2.0
        
        # 4. Pre-calculate Camera Group Centers in the Payload Frame
        # We perform the offset in the Master Frame to ensure rigid geometry
        self.camera_centers_xy = self._calculate_camera_positions()

    def _calculate_camera_positions(self):
        """
        Calculates the (Lon, Lat) offsets of the 4 camera groups in the Payload Frame.
        Returns a list of tuples: [(x1, y1), (x2, y2), ...]
        """
        centers = []
        for az in self.camera_azimuths:
            # Create a coordinate at the correct distance/angle from center
            # Then transform it immediately to the Payload Frame to get (X, Y)
            c_sky = self.payload_center.directional_offset_by(
                position_angle=az, 
                separation=self.camera_offset_dist
            )
            c_local = c_sky.transform_to(self.payload_frame)
            
            # Store the projected X/Y (Lon/Lat)
            centers.append({
                'x': c_local.lon,
                'y': c_local.lat,
                'sky_coord': c_sky # Kept for the spherical circle check
            })
        return centers

    def check_observation(self, ra, dec):
        # 1. Transform Target to the Master Payload Frame
        target = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        target_local = target.transform_to(self.payload_frame)
        
        # Get X/Y of target in Payload Frame
        # wrap_at(180) ensures we deal with -180 to +180 range
        t_x = target_local.lon.wrap_at(180 * u.deg)
        t_y = target_local.lat
        
        camera_group_counts = np.zeros(np.shape(ra), dtype=int)
        
        for cam in self.camera_centers_xy:
            # --- A. Check Spherical Circle ---
            # (Strictly speaking, the circle is optical, so it's a cone on the sky.
            # We use the true spherical separation for this part.)
            sep = cam['sky_coord'].separation(target)
            in_circle = sep < self.circle_radius
            
            # --- B. Check Square & Gaps (In Payload Frame) ---
            # Calculate distance from this camera's center in X and Y
            # Note: Since everything is in the SAME frame, parallel lines are guaranteed.
            dx = np.abs(t_x - cam['x'])
            dy = np.abs(t_y - cam['y'])
            
            # 1. Inside Square?
            in_square = (dx < self.square_half_width) & \
                        (dy < self.square_half_width)
            
            # 2. Outside Gap? (The "Dead Cross" centered on the camera)
            not_in_gap = (dx > self.gap_half_width) & \
                         (dy > self.gap_half_width)
            
            # Combine
            visible = in_circle & in_square & not_in_gap
            camera_group_counts += visible.astype(int)
            
        return camera_group_counts


# --- Updated Execution Block ---
if __name__ == "__main__":
    # 1. Set up Argument Parser
    parser = argparse.ArgumentParser(
        description="Calculate PLATO space telescope coverage for specific coordinates or batch files."
    )
    
    # Batch File Argument
    parser.add_argument(
        "--file", 
        type=str, 
        help="Path to a CSV file containing 'ra' and 'dec' columns."
    )
    
    # Single Target Arguments
    parser.add_argument("--ra", type=float, help="Right Ascension in degrees (ICRS).")
    parser.add_argument("--dec", type=float, help="Declination in degrees (ICRS).")
    
    # Optional: Keep the stats functionality
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Run the Monte Carlo simulation to estimate total field of view areas."
    )

    args = parser.parse_args()

    # 2. Initialize the Model
    # (We do this once so it's ready for any mode)
    try:
        plato = PlatoPoint()
    except Exception as e:
        print(f"Error initializing PlatoPoint model: {e}")
        sys.exit(1)

    # 3. Handle Modes
    
    # --- Mode A: Batch CSV Processing ---
    if args.file:
        try:
            print(f"Reading {args.file}...")
            df = pd.read_csv(args.file)
            
            # Normalize column names to lowercase for checking
            df.columns = [c.lower() for c in df.columns]
            
            if 'ra' not in df.columns or 'dec' not in df.columns:
                print("Error: CSV input must contain 'ra' and 'dec' columns.")
                sys.exit(1)
                
            print(f"Calculating coverage for {len(df)} sources...")
            
            # Run the check
            counts = plato.check_observation(df['ra'].values, df['dec'].values)
            
            # Add results to dataframe
            df['n_camera_groups'] = counts
            
            # Save output
            output_file = "plato_coverage_output.csv"
            df.to_csv(output_file, index=False)
            print(f"Success! Results saved to '{output_file}'.")
            
        except FileNotFoundError:
            print(f"Error: The file '{args.file}' was not found.")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred during processing: {e}")
            sys.exit(1)

    # --- Mode B: Single Target Check ---
    elif args.ra is not None and args.dec is not None:
        count = plato.check_observation(args.ra, args.dec)
        # check_observation returns an array, so extract the item
        n_cams = int(count) if np.ndim(count) == 0 else int(count[0])
        
        print(f"\nTarget coordinates: RA {args.ra}, Dec {args.dec}")
        print(f"Number of observing camera groups: {n_cams}")
        if n_cams > 0:
            print("Status: OBSERVED")
        else:
            print("Status: OUTSIDE FIELD OF VIEW")

    # --- Mode C: Statistics ---
    elif args.stats:
        stats = plato.calculate_coverage_breakdown()
        print(f"\n{'Multiplicity':<15} | {'Area (deg²)':<15}")
        print("-" * 35)
        for n in [4, 3, 2, 1]:
            print(f"{n} Cameras       | {stats[n]:8.2f}")
        print("-" * 35)
        print(f"TOTAL Field     | {stats['Total']:8.2f}")

    # --- Error Handling for Missing Args ---
    else:
        # Check if user provided only one of RA/Dec
        if (args.ra is not None) ^ (args.dec is not None):
            print("Error: You must provide BOTH --ra and --dec.")
        else:
            parser.print_help()
