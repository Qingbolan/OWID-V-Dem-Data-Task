Source: https://ourworldindata.org/regimes-of-the-world-data

# The “Regimes of the World” data: how do researchers measure democracy?

## There are many ways to measure democracy. Here is how the Regimes of the World classification, one of the leading sources of global democracy data, does it.

Measuring the state of democracy across the world helps us understand the extent to which people have political rights and freedoms.

But measuring democracy comes with many challenges. People do not always agree on what characteristics define a democracy. These characteristics — such as whether an election was free and fair — are difficult to define and assess. The judgment of experts is to some degree subjective. They may disagree about a specific characteristic or how something as complex as a political system can be reduced into a single measure.

How do researchers address these challenges and measure democracy?

# What is the Regimes of the World data?

In some of our work on democracy, we rely on the Regimes of the World (RoW) data by political scientists Anna Lührmann, Marcus Tannenberg, and Staffan Lindberg 1 , published by the Varieties of Democracy (V-Dem) project . 2

The project is managed by the V-Dem Institute, based at the University of Gothenburg in Sweden. It spans seven more regional centers around the world and is run by five principal investigators, dozens of project and regional managers, and more than 100 country coordinators.

V-Dem is funded through grants and donations by government agencies and private foundations, such as the Swedish Research Council, the European Commission, and the Marcus and Marianne Wallenberg Foundation.

# How does RoW characterize democracy?

Regimes of the World distinguishes four types of political systems: closed autocracies, electoral autocracies, electoral democracies, and liberal democracies.

Closed autocracy : citizens do not have the right to choose either the chief executive of the government or the legislature through multi-party elections

Electoral autocracy : citizens have the right to choose the chief executive and the legislature through multi-party elections; but they lack some freedoms, such as the freedoms of association or expression that make the elections meaningful, free, and fair

Electoral democracy : citizens have the right to choose the chief executive and the legislature in meaningful, free and fair, and multi-party elections

Liberal democracy : electoral democracy and citizens enjoy individual and minority rights, are equal before the law, and the actions of the executive are constrained by the legislative and the courts

You can find data on the more specific characteristics and derived measures in our Democracy Data Explorer .

# How is democracy scored?

Regimes of the World treats democracy as a binary, by classifying a country as either a democracy or not.

This scoring thereby differs from other approaches such as Varieties of Democracy’s electoral democracy index and other projects , which classify countries as a spectrum, with some being scored as more democratic than others.

[FIG 01: 01 Democracy]

# What years and countries are covered?

As of version 16 of the dataset, V-Dem covers 202 countries, going back in time as far as 1789. Many countries have been covered since 1900, including before they became independent from their colonial powers.

RoW covers countries and years since 1900. But we expand the years and countries covered and refine the coding rules, as detailed below.

# How is democracy measured?

## How does RoW work to make its assessments valid?

To measure what it wants to capture, RoW uses data from the Varieties of Democracy project, which assesses the characteristics of democracy mostly through evaluations by experts. 3

These anonymous experts are primarily academics and members of the media and civil society. They are also often nationals or residents of the country they assess, and therefore know its political system well and can evaluate aspects that are difficult to observe.

V-Dem’s own team of researchers supplements the expert evaluations. They code some easier-to-observe rules and laws of the political system, such as whether the legislature has a lower and upper house.

## How does RoW work to make its assessments precise and reliable?

V-Dem uses several experts per country, year, and topic, to make its assessments less subjective. In total, V-Dem relies on more than 4,000 country experts.

While there are fewer experts for small countries and for the time before 1900, they rely on an average of 38 experts per country and 5 experts per topic.

## How does RoW work to make its assessments comparable?

V-Dem also works to make their coders’ assessments comparable across countries and time.

The surveys ask the experts to answer very specific questions on completely explained scales about sub-characteristics of political systems — such as the presence or absence of election fraud — instead of making them rely on their broad impressions.

The surveys are available in English, Arabic, French, Portuguese, Russian, and Spanish to reduce misunderstandings.

Experts further evaluate hypothetical countries, many coded several countries, and they denote their own uncertainty and personal demographic information.

V-Dem then uses this information to investigate expert biases, which they have found to be limited: they only find that experts from a country tend to be stricter in their assessments. 4

## How are the remaining differences in the data dealt with?

V-Dem uses a statistical model to address any remaining differences between coders. 5

The model combines the experts’ ratings of actual countries and hypothetical countries, as well as the experts’ stated uncertainties and personal demographics to produce best, upper-, and lower-bound estimates of many characteristics. 6

V-Dem provides these different estimates for all of its main and supplementary indices, including the Electoral Democracy Index and the subindices for free and fair elections, freedom of association, and freedom of expression.

With the different estimates, V-Dem explicitly acknowledges that its coders can be uncertain or make errors in their measurement.

In addition to its main classification, RoW provides an expanded version that identifies countries that may fit better into the next-higher or -lower main categories. You can find the data in our Democracy Data Explorer .

The overall classification is the result of evaluating whether necessary characteristics are present or not. If the experts consider a country’s elections to have been both multi-party and free and fair, and the country as having had minimal features of an electoral democracy in general 7 , RoW classifies it as a democracy.

A country is classified as a liberal democracy if the experts consider the country’s laws to have been transparent; the men and women there as having had access to the justice system; and the country as having had broad features of a liberal democracy overall. 8 If it does not meet one of these conditions, the country is classified as an electoral democracy.

A country is classified as an autocracy if it does not meet the above criteria of meaningful, free and fair, multi-party elections. It is classified as an electoral autocracy if the experts consider the elections for the legislature and chief executive — the most powerful politician — to have been multi-party. It is classified as a closed autocracy if either the legislature or chief executive has not been chosen in multi-party elections.

## How is the data made accessible and transparent?

V-Dem, which publishes the RoW data, releases its data publicly and makes it straightforward to download and use.

It publishes the overall scores, the underlying subindices, and several hundred specific questions by country-year, country-date, and coder.

V-Dem also releases descriptions of how RoW measures democracy, as well as the questions and coding procedures that guide the experts and researchers.

# How do we change the data?

In our work, we expand the years covered by RoW further.

While RoW covers the years since 1900, we use V-Dem's historical data from 1789 to 1899 to expand the classification’s coverage back in time.

To expand the time coverage of today’s countries and include more of the period when they were still non-sovereign territories, we identified the historical entity they were a part of and used that regime’s data whenever available. 9

Finally, we make some additional smaller changes. 10

# How often and when is the data updated?

V-Dem releases a new version of the data each year in March.

We at Our World in Data aim to update our data within a few weeks of the release.

# What are the data’s shortcomings?

There are shortcomings in the way Regimes of the World characterizes and measures democracy. 11

The classification only captures that these political rights were broad, not that they were universal. This means that not all people living in a democracy necessarily enjoy its political rights: this includes children, but often also historically marginalized groups such as women. 12

The classification also focuses on electoral and liberal understandings of democracy and does not account for other characterizations, such as democracies as egalitarian political systems, in which political power is equally distributed to allow everyone to participate. This means that some of the most economically-unequal countries in the world, such as Brazil and South Africa, are classified as broadly democratic in recent years.

RoW also does not cover some countries with very small populations.

Furthermore, because the classification groups all political systems into four broad types, it is not very granular. This means that it does not pick up small changes in political institutions, or conversely that the classification sometimes categorizes countries with similar institutions differently. This includes some recategorizations of countries across years where their political institutions barely changed, but crossed a somewhat arbitrary threshold. 13

The assessment of the RoW classification remains to some extent subjective. It is built on difficult evaluations by experts that rely less on easier-to-observe characteristics, such as whether regular elections are held.

Finally, the index’s aggregation remains to some extent arbitrary. It is unclear why specific indicators were chosen, such as whether citizens had access to the justice system, and not (also) whether they were free from government repression.

# What are the data’s strengths?

Despite these shortcomings, the classification tells us a lot about how democratic the world was in the past and today.

Its characterizations of democracy as an electoral political system, in which citizens get to participate in free and fair elections, and a liberal political system, in which citizens are protected from others and the state, are commonly recognized as the two basic principles of democracy and shared by most of the leading approaches of measuring democracy .

Because it treats democracy as a binary, the classification can make the many differences in political institutions we observe across countries and over time much easier to understand. It allows us to combine the many countries with similar political institutions, while still distinguishing countries whose institutions differ in meaningful ways. This allows us to observe whether one country is democratic or not, or whether a country has become a democracy or stopped being one over time.

The index also covers many countries and years. Except for microstates, it covers all countries in the world. Many countries are covered since 1900 — even while they were colonized by another country — and some of them as far back as 1789.

Finally, RoW and V-Dem take many steps to make their assessments valid, precise, comparable across countries and time, and transparent. RoW relies on many country and subject experts answering detailed surveys to measure aspects of political systems that are often difficult to observe, and acknowledges the remaining uncertainty in their assessments in its expanded classification.

# What is our summary assessment?

Whether the Regimes of the World classification is a useful measure of democracy will depend on the questions we want to answer.

The classification will not give us a satisfying answer if we are interested in the political rights of historically marginalized groups specifically; in non-electoral or non-liberal understandings of democracy; in the political systems of microstates; and interested in small differences in the political systems of countries.

In these cases, we will have to rely on other measures .

But if we value a sophisticated measure based on the knowledge of many country experts and are interested in big differences in political regimes, within and across countries, and far into the past, we can learn a lot from this data.

It is for these latter purposes we use the measure in some of our reporting on democracy.

## Keep reading on Our World in Data

## Acknowledgments

I thank Marcus Tannenberg and Johannes von Römer for providing data and code, and Edouard Mathieu, Hannah Ritchie and Max Roser for their very helpful comments and ideas about how to improve this article.

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
