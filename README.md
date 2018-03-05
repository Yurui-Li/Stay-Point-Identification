# Stay-Point-Identification

A stay point is a geographic region that a person has stayed for a period of time.we propose a new method called SPID(Stay Point Identification based on Density) for stay point identification from individual GPS trajectories. SPID take into account two directions of time continuity to compute density. We select candidate points according to the principle of the maximum likelihood and adopt the strategy that uses the information of the existing stay points to update the candidate point.

#Information Note
This is an paper under review, we will give the link address after the paper was published.
#Dataset
We use GeoLife dataset [16], collected in (Microsoft Research Asia) GeoLife project by 182 users in a period of over three years (from April 2007 to August 2012). This dataset contains 17,621 trajectories with a total distance of 1,292,951kilometers and a total duration of 50,176 hours.These trajectories were recorded by different GPS loggers and GPS-phones and have a variety of sampling rates. 91.5 percent of the trajectories are logged in a high frequency,e.g., every 1~5 seconds or every 5~10 meters per point.
Here is the [website address](http://research.microsoft.com/en-us/downloads/b16d359d-d164-469e-9fd4-daa38f2b2e13/)
#Baseline Algorithm
We take the approach used in the literature (Li, Quannan, et al. "Mining user similarity based on location history." ACM Sigspatial International
Conference on Advances in Geographic Information Systems ACM, 2008:34) as the baseline algorithm.