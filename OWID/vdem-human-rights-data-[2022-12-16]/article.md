Source: https://ourworldindata.org/vdem-human-rights-data

# The 'Varieties of Democracy' data: how do researchers measure human rights?

## There are several ways to measure human rights. Here is how the Varieties of Democracy project does it, one of the leading sources of human rights data.

Measuring the state of human rights across the world helps us understand the extent to which people have fundamental personal and civil rights and freedoms.

But it can be challenging to measure how well-protected these human rights are.. People do not always agree on what rights are fundamental. These rights — such as whether people are free to voice their opinions — are difficult to define and assess. The judgement of experts is to some degree subjective. They may disagree about a specific characteristic or how several characteristics can be reduced into a single measure.

How do researchers address these challenges and measure how much people’s human rights are protected?

# What is the Varieties of Democracy project?

In some of our work on democracy, we rely on data published by the Varieties of Democracy (V-Dem) project . 1

The project is managed by the V-Dem Institute, based at the University of Gothenburg in Sweden. It spans seven more regional centers around the world and is run by five principal investigators, dozens of project and regional managers, and more than 100 country coordinators.

V-Dem is funded through grants and donations by government agencies and private foundations, such as the Swedish Research Council, the European Commission, and the Marcus and Marianne Wallenberg Foundation.

# How does V-Dem characterize human rights?

Our team at Our World in Data uses V-Dem’s Civil Liberties Index to measure human rights.

V-Dem characterizes civil liberties as three types of freedoms: physical integrity rights, private civil liberties, and political civil liberties. More specifically, this means:

Physical integrity rights : people are free and protected from government torture and political killings

Private civil liberties : people are free from forced labor, have property rights, and enjoy freedoms of movement (move unrestricted within, to, and from the country) and religion (choose and practice their faith)

Political civil liberties : people enjoy freedoms of association (parties and civil society organizations can form and operate freely) and expression (they can voice their views, and the media can present different political perspectives)

# How are human rights scored?

V-Dem’s Civil Liberties Index scores each country on a spectrum, with some countries protecting human rights more than others.

The spectrum ranges from 0 (‘fewest rights’) to 1 (‘most rights’).

[FIG 01: 01 Human Rights Index]

# What years and countries are covered?

As of version 12 of the dataset, V-Dem covers 202 countries, going back in time as far as 1789. Many countries have been covered since 1900, including before they became independent from their colonial powers.

# How are human rights measured?

## How does V-Dem work to make its assessments valid?

To actually measure what it wants to capture, V-Dem assesses the characteristics of human rights mostly through evaluations by experts. 2

These anonymous experts are primarily academics and members of the media and civil society. They are also often nationals or residents of the country they assess, and therefore know its political system well and can evaluate aspects that are difficult to observe.

V-Dem’s own team of researchers supplements the expert evaluations. They code some easier-to-observe rules and laws of the political system, such as whether the legislature has a lower and upper house.

## How does V-Dem work to make its assessments precise and reliable?

V-Dem uses several experts per country, year, and topic, to make its assessments less subjective. In total, around 3,500 country-experts fill surveys for V-Dem every year.

While there are fewer experts for small countries and for the time before 1900, they rely typically on 25 experts per country and 5 experts per topic.

## How does V-Dem work to make its assessments comparable?

V-Dem also works to make their coders’ assessments comparable across countries and time.

The surveys ask the experts to answer very specific questions on completely explained scales about sub-characteristics of human rights — such as whether women can freely move in their own country — instead of making them rely on their broad impressions.

The surveys are available in English, Arabic, French, Portuguese, Russian, and Spanish to reduce misunderstandings.

Experts further evaluate hypothetical countries, many coded several countries, and they denote their own uncertainty and personal demographic information.

V-Dem then uses this information to investigate expert biases, which they have found to be limited: they only find that experts from a country tend to be stricter in their assessments. 3

## How are the remaining differences in the data dealt with?

V-Dem uses a statistical model to address any remaining differences between coders. 4

The model combines the experts’ ratings of actual countries and hypothetical countries, as well as the experts’ stated uncertainties and personal demographics to produce best, upper-, and lower-bound estimates of many characteristics. 5

V-Dem provides these different estimates for all of its main and supplementary indices, including the Civil Liberties Index and the subindices for physical integrity rights, private civil liberties, and political civil liberties.

With the different estimates, V-Dem explicitly acknowledges that its coders can be uncertain or make errors in their measurement.

The overall Civil Liberties Index score is the result of averaging the three subindices.

## How is the data made accessible and transparent?

V-Dem releases its data publicly, and makes it straightforward to download and use.

It publishes the overall scores, the underlying subindices, and several hundred specific questions by country-year, country-date, and coder.

V-Dem also releases detailed descriptions of the questions and coding procedures that guide the experts and researchers.

# How do we change the data?

In our work, we expand the years covered by V-Dem further.

To expand the time coverage of today’s countries and include more of the period when they were still non-sovereign territories, we identified the historical entity they were a part of and used that regime’s data whenever available. 6

We also calculated regional and global averages of the Civil Liberties Index and its sub-indices, weighted and unweighted by population.

Our code and data are available on GitHub and record our revisions in detail.

# How often and when is the data updated?

V-Dem releases a new version of the data each year in March.

We at Our World in Data aim to update our own data within a few weeks of the release.

# What are the shortcomings of the data?

There are shortcomings in the way that V-Dem’s Civil Liberties Index characterizes and measures human rights. 7

The index focuses on human rights as civil liberties and does not account for other characterizations, such as rights to food, health, or education. This means that countries with good health and education outcomes but restricted civil liberties, such as Iran and Singapore in recent years, still receive relatively low scores.

The index also does not tell us anything about how human rights differ across parts of the population, such as between men and women, or between different ethnic groups. 8

V-Dem also does not cover some countries with very small populations.

Furthermore, the index is more difficult to interpret than other measures. The Civil Liberties Index does not identify whether a country grants or protects human rights or not, but only allows us to say whether a country is protecting human rights by comparing it to the range of the index, to other countries, or to the same country at another point in time. And when doing so, it is still difficult to say how large these differences are. 9

The assessment of the Civil Liberties Index remains to some extent subjective. Its index is built on difficult evaluations by experts and relies less on easier-to-observe characteristics, such as whether forming a civil society organization independent of the state is legal, or the number of allegations made in human rights reports against the government.

Finally, the index’s aggregation remains to some extent arbitrary. V-Dem does not say why these specific subindices were chosen, and why the subindices are given the same weight.

# What are the data’s strengths?

Despite these shortcomings, the index tells us a lot about how protected human rights are around the world, in the past and today.

Its characterization of human rights as people enjoying physical integrity, as well as private and political civil liberties, is commonly recognized to be at the core of human rights.

Because it treats human rights as a spectrum, the index is able to capture both big and small differences in their protection across countries, and to record small changes within countries over time. This allows us to observe whether one country protects human rights more than another, or whether a country has protected human rights more or less over time.

The index also covers many countries and years. With the exception of microstates, it covers all countries in the world. Many countries are covered since 1900 — even while they were colonized by another country — and some of them as far back as 1789.

Finally, V-Dem takes many steps to make its assessments valid, precise, comparable across countries and time, and transparent. It relies on many country and subject experts answering detailed surveys to measure aspects of political systems that are often difficult to observe and acknowledges the remaining uncertainty in their assessments.

# What is our summary assessment?

Whether V-Dem’s Civil Liberties Index is a useful measure of human rights will depend on the questions we want to answer.

The index will not give us a satisfying answer if we are interested in an understanding of human rights as also including rights to health or education; in differences in the protection of human rights by gender and ethnicity; and if we are also interested in the political systems of microstates.

In these cases, we may have to rely on other measures .

But if we value a sophisticated measure based on the knowledge of many country experts and are interested in big and small differences in civil liberties, within and across countries, and far into the past, we can learn a lot from this data.

It is for these latter purposes we use the measure in some of our reporting on human rights.

## Keep reading on Our World in Data

## Acknowledgments

I thank Edouard Mathieu for his very helpful comments and ideas about how to improve this article.

### Endnotes

### Cite this work

Our articles and data visualizations rely on work from many different people and organizations. When citing this article, please also cite the underlying data sources. This article can be cited as:

BibTeX citation

### Past versions

We are a live site and we keep our work maintained. So our articles are often changed, including the data. You can browse previous versions of this work here.

### Reuse this work freely

All visualizations, data, and articles produced by Our World in Data are completely open access under the Creative Commons BY license . You have the permission to use, distribute, and reproduce these in any medium, provided the source and authors are credited.

The data produced by third parties and made available by Our World in Data is subject to the license terms from the original third-party authors. We will always indicate the original source of the data in our documentation, so you should always check the license of any such third-party data before use and redistribution.

All of our charts can be embedded in any site.
