# FISH! Rod Optimizer

A desktop tool to find the perfect fishing gear combination for FISH! which is a VR-based fishing title based within the popular free to play game VRChat. Stop guessing which rod and bobber to use and let math do the work!

##  Features
* **Custom Priority:** Rank stats like Luck, Strength, and Expertise, Attraction, Big Catch, and Max Weight.
* **Smart Filtering:** Options to exclude Quest or Reward-only items and make all selections weighted evenly
* **Total Cost Calculation:** See exactly how much your new build will cost.

##  How to Run
### For Users (Fastest)
1. Go to the [Releases](https://github.com/kaspian-slate/FISH-rod-optimizer/releases/tag/v1.0.0) page.
2. Download `Fish_Rod_Optimizer.exe`.
3. Run and start optimizing! 
   *(Note: You may need to click "Run Anyway" if Windows Defender flags it as an unrecognized app.)*

### For Developers
If you want to run from source:
1. Clone this repo.
2. Install requirements: `pip install -r requirements.txt`.
3. Run `python app.py`.

##  How it Works
The optimizer takes all possible combinations of Rods, Lines, and Bobbers and calculates a "weighted score" based on your priorities. It then normalizes the stats to ensure a fair comparison across different units.
