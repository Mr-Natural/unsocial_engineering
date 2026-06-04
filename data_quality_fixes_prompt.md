# Data Quality Fixes — Price Guards, Hospital Definition, Vets

Read CLAUDE.md before starting.

## 1. Minimum Sample Guard for Headline Price

Sydney CBD shows a $109.43M median house price from 1-2 ultra-premium sales. Fix this:

- If fewer than 5 house sales across the trailing 4 quarters, don't display median house price as the headline. Show median unit price instead.
- Update the direct answer summary template (the AI-optimised paragraph at the top of suburb pages) to use whichever price type has more sales in the trailing 4 quarters.
- If both house and unit have fewer than 5 sales, show "Limited sales data" instead of a price.
- Update the hero stat bar to reflect the same logic.
- Verify with: Sydney CBD, Barangaroo, and other unit-dominated suburbs should show unit price as headline. Suburbs with normal house sales volume should be unaffected.

## 2. Tighten Hospital Definition

The current OpenStreetMap `amenity=hospital` tag includes day surgeries, medical centres, and aged care facilities. Fix this:

- In load_amenities.py, update the hospital query to filter for genuine hospitals only. Use one or more of:
  - `emergency=yes` tag (most reliable indicator of a real hospital)
  - `healthcare=hospital` tag
  - Exclude facilities with `healthcare=clinic`, `social_facility=*`, or `healthcare:speciality=surgery` where they don't also have `emergency=yes`
- Re-run the hospital amenity count for all suburbs
- Update the `hospitals_nearby` count (within 5km) and the `hospital_km` / `hospital_name` in distances JSONB
- Verify: major hospitals (Westmead, Royal North Shore, St George, Liverpool) should still be counted. Day surgery centres and medical centres should be excluded.

## 3. Add Veterinary Clinics

Pet owners are a key demographic for suburb research. Add vet data:

- In load_amenities.py, add an Overpass query for `amenity=veterinary` across NSW
- Count vets per suburb, store in liveability `extra_data` JSONB under key `veterinary`
- In load_distances.py, add `vet_km` and `vet_name` to the distances JSONB (nearest vet from suburb centroid)
- On the suburb profile page liveability card, add vets to the amenities grid with a paw print icon (or similar)
- Re-run load_amenities.py for the new type and load_distances.py for vet distances
- Refresh the materialised view after

## After all fixes:
- Re-run scripts/audit_data.py to verify benchmark suburbs
- Run scripts/site_test.py to confirm no regressions
- Push to GitHub

## Definition of done
- Sydney CBD shows unit price as headline, not $109M house price
- Hospital counts reflect genuine emergency hospitals only
- Veterinary clinics counted and displayed on suburb profiles
- Nearest vet distance in JSONB
- All tests pass
- Pushed to GitHub
