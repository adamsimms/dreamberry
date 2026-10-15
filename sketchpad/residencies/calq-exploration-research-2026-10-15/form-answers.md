# CALQ Exploration and Research: filed copy

**Program:** Exploration and Research, Digital arts
**Form:** Mon Dossier
**Status:** Submitted 2026-10-15
**Issue:** [dreamberry#50](https://github.com/adamsimms/dreamberry/issues/50)
**Language:** English
**Project dates:** 1 December 2026 to 15 April 2027
**Amount requested:** $25,000
**Personal contribution on the form:** $1,402
**Revenues and expenses:** $26,402
**Other organizations:** No. Rover CALQ was not filed.

This is the copy that matches the submitted form. The Newfoundland paragraph is the one confirmed after the schedule screenshot. It is a filed snapshot, not a living contract.

Support PDFs in this folder are the three files named at submit:

| File | Pages | On disk |
|---|---|---|
| `Adam-Simms-CV-CALQ.pdf` | 3 | 2026-10-14 15:18 |
| `Adam-Simms-Press-CALQ.pdf` | 3 | 2026-10-14 15:19 |
| `Adam-Simms-Support-Materials-CALQ.pdf` | 10 | 2026-10-15 09:12 |

---

## Description

CONTEXT

In the 1960s, my grandmother’s house floated across the bay on a barge. Every house on Pinchard’s Island made the same trip, towed by boat to communities the Newfoundland government had designated as growth centres. Doris was born and raised on the island, and like everyone else, she resettled. All that remains of the original community is a graveyard and the memories of the people who lived there; both are slowly disappearing.

Decades after the island emptied, my family began returning, and eventually we built an off-grid cabin there. In 2017, I mounted Cloudberry, a solar-powered camera system I designed, on that cabin. It autonomously photographed the island while I watched from Montréal and my family watched from their homes in Newfoundland. Across thousands of frames, it held one view as the weather changed. It also failed in its own ways: sometimes it went silent for days or sent back black frames in full daylight. Eventually the cold and too little sun forced it to sleep. It never invented a frame.

Dreamberry is the sleeping camera dreaming the view from the cabin window, steered by live weather at the island’s coordinates. In this research and exploration, I will train an image model on every photograph Cloudberry made, then feed the model its own dreams, one generation after another, until the island begins to drift. I want to see how much of a place a machine can hold, and how it forgets.

Two distances separate me from Pinchard’s Island, one of time and one of space. I know the resettlement only as my family tells it, which is close to what Marianne Hirsch calls postmemory: a memory that arrives secondhand and incomplete. After more than half my life away from Newfoundland, I am both of the place and outside it. What I try to carry across both distances is less an object than something said or done: Uncle Bob’s cove names that appear on no map, the way Doris bottles beets, words I have heard nowhere else.

Distance is the material of my work. For a decade I have built systems to keep the island within reach, designing both the hardware and the code. In Cabin, a Newfoundland hearth rebuilt in a Montréal high-rise looks out on the island through Cloudberry’s live feed. In Driftwood, a sea-weathered log echoes the North Atlantic’s movement, read live from an offshore buoy. In Light House, a solar-powered outline of a house glows at the edge of the shore. In each, presence is partial, remote and permitted to fail.

RESEARCH

This research period asks what happens to a place when a machine is left to remember it. Three questions drive it:

1. What can a machine hold of a place it knows only from photographs?

General-purpose image generators rest on the premise that more material means more fluency, so their makers take in everything they can reach. This research does the opposite. The model learns from thousands of photographs of a single view on Pinchard's Island, so it knows the place only through what was documented. The corpus is also small enough that its gaps can be named by the people who remember the island: what it leaves out, and later, what the model forgets.

The model knows the island only as patterns in pixels; a viewer meets it as a place. Gernot Böhme argues that people meet a place first as atmosphere, and Andy Clark describes perception as prediction, the eye completing what it is not given. Jim Campbell’s LED works ask how little a picture needs before it stops being one. I want to know how far the island can be reduced to light and still be felt as a place, and how much of it a viewer supplies from what the light leaves out.

2. How does a machine forget a place: what goes first, and what survives longest?

Shumailov and colleagues showed in Nature in 2024 that models trained on their own output lose what is rare in their data and drift toward the middle, eventually offering something plausible in place of something true. The industry works to prevent this collapse. At the scale of general-purpose models, the forgetting cannot be seen, because no one can say what was lost when no one knew what was there. A resettled place is lost the same way: once the last people who remember it are gone, no one can say what is missing. Here, what was there is still known: one view, and the people who remember it. Rather than prevent the collapse, this research invites it, because a machine that stands in for a place will also forget it, and I want to see what that forgetting looks like in the open. What Dreamberry keeps of the island and what it loses are both results.

3. What does a machine assert when it keeps dreaming images of resettled, colonized ground?

The third question cannot be answered by the machine alone. Pinchard’s Island lies within Ktaqmkuk, and its Beothuk and Mi’kmaq histories predate the outport Doris was born into. I cannot assume that an apparatus making images of that ground is innocent of the erasure that made the community possible. Tuck and Yang’s refusal of decolonization as a metaphor is the warning I keep in view. Indigenous scholarship on land and on artificial intelligence, including the work of Glen Coulthard and Jason Edward Lewis, will shape what I ask of such a machine, and the people in the experimentation workshops will carry the question further.

Resettlement is not only Newfoundland history. In 1970, Québec planned to close ninety-six localities in the Est-du-Québec and move more than sixty thousand people. Ten were closed by decree, and their houses were burned so that no one could return, until Opérations Dignité stopped the program and the policy became aménagement rather than déménagement. Where the houses of Pinchard’s Island were floated away, those were set to burn. Who is permitted to stay remains a live argument beyond these two histories. Communities in Canada and elsewhere are still being displaced by policy, by industry and now by rising seas, and this research stays with that argument.

For this research period, the questions are meant to stay open and evolve. I will draw on academic texts on topics that inform these questions: postmemory, the perception of atmosphere and of low-resolution images, model collapse, and Indigenous scholarship on land and artificial intelligence. A working bibliography is underway and will grow with the research. I expect the questions to shift as the explorations described below unfold.

EXPLORATIONS

I will pursue these questions along three lines of exploration: training an image model, building low-resolution display prototypes, and running experimentation workshops with three audiences. The work moves between my studio in Montréal, a residency at the Arteles Creative Center in Haukijärvi, Finland, where I have been accepted to the Silence Awareness Existence residency, and my family home in Newfoundland.

In my Montréal studio, I will train the image model on the Cloudberry photographs and experiment with the parameters that govern the look and behaviour of its dreams. The history of Pinchard’s Island reached me as retellings of retellings, and the model will learn the same way. In a fast loop, its dreams are fed back into its training to see what each retelling keeps. In a slower loop, the original photographs are retired a few at a time and replaced by its own images, so the Cloudberry archive gradually ages out of its memory. The pace of that slower loop may be left to chance or tied to an outside variable, so its end cannot be known in advance; what I will observe is the rate and order of forgetting. Hiroshi Sugimoto spent decades photographing seas around the world with the horizon at the same height, until one could hardly be told from another. His sameness was chosen. The model’s is a loss, reached by arithmetic rather than devotion, and potentially much faster.

To read that forgetting, I will measure each generated image against the archive in two ways. The first is how far it sits from the nearest real photograph, a single number that catches drift. The second is how far the images in a batch sit from one another, which shows the model losing variety. I will record both throughout, so the shape of the forgetting can be read beside the images themselves.

In parallel, I will build a low-resolution window prototype to display the generated images. I will begin with interchangeable LED panels at different pixel pitches and test them behind a range of acrylic diffusers, adding or swapping materials as the results suggest. Pitch and diffusion will be varied independently because they do different work: pitch determines how much of the view is present at all, while the diffuser decides whether a viewer reads separate points of light or one continuous field. The threshold where light is still felt as the island likely sits somewhere in their combination, so the prototype is built to be taken apart and rebuilt rather than fixed to one specification. One question to test is whether each dream can reach a viewer as a field of coloured light, slowly fading into the next as the island’s weather changes. At a glance it might read as a still image; with a longer look, I hope it reads as weather passing. I will source the parts in Montréal, carry them to Finland with spare diffusers, and test the prototype through the residency, where a month of studio time and silent days suit slow work with hardware and long looking.

I will also run experimentation workshops with three groups at three distances from the island. At Arteles, they are artists who have never heard of Pinchard’s Island. In Montréal, they are my peers at the Milieux Institute: members of the Post Image cluster, who make and read photographs professionally and know my earlier work, and members of the Indigenous Futures cluster, invited especially to respond to what the work asserts about Indigenous land. In Newfoundland, they are locals, including family members who lived on Pinchard’s Island. Each workshop shares the same format, while what I show evolves from one to the next: a cold read first, where people say what they see before I explain anything, then the context, then their feedback, documented with their consent. I will record what changes between workshops and why, so the evolution itself becomes part of the research.

## Anticipated benefits

The most direct benefit is a record and a specification. The record holds the generated images and their measurements, the prototype configurations and how each one reads, and notes from the three workshops. From it comes a specification for a full-scale Dreamberry artwork, based on what the explorations showed and what they ruled out: the model and its parameters, the pitch and diffusion the window needs, and how a generated view holds the island as it begins to disappear. A separate creation project, following this research and exploration period, would start from those findings.

This research extends a decade of practice in a new direction. So far, I have built machines that record, and the problems they posed were problems of transmission. A machine that invents raises different questions. Working through them, alongside arguments about what these technologies take and what they assert, gives me a critical frame for the subjects my work has always circled: belonging, displacement and intangible culture. My hope is to find a new way to record places that outlast the people who remember them, one that carries some of that memory forward while keeping the loss visible rather than repaired.

For the past ten years I have funded my own research and work through a parallel career as a software designer and developer. This is my first application to the Conseil des arts et des lettres du Québec, and support for this period would let me focus on the practice rather than client work.

The month at Arteles, in February 2027, puts my research in front of an international cohort. The residency’s Silence Awareness Existence program is built for the attention this research needs: a month to sit with the explorations rather than to produce a final work.

What remains afterward is not only mine. I will release the training and collapse-loop code under an open-source licence, together with a record of what this model lost as it consumed its own dreams, so that other artists and researchers can use it, adapt it, and run it on their own material.

## Remuneration

I am the only person paid from this grant. The remuneration rate is $40 an hour, within the CARFAC-RAAV recommended hourly range for artists’ professional services. The stipend covers my research and exploration labour.

Full-time at the Arteles residency and in Newfoundland: 30 hours a week at $1,200 per week for 6 weeks = $7,200.

Part-time in Montréal: 15 hours a week at $600 per week for 13 weeks = $7,800.

Stipend total: $15,000.

No other artists are engaged on the project. Up to five people take part in each of the three experimentation workshops, at Arteles, in my Montréal studio and in Newfoundland. Each receives $40 for a one-hour session as a research participant, with written consent, for a total of $600.

## Schedule

Activity 1. Model training and defining the loop

From 2026-12-01 to 2026-12-31. Place: Montréal, Québec.

I train the model on the Cloudberry photographs and experiment with the parameters that govern the look and behaviour of its dreams. The work here is defining the loop: how quickly dreams enter the corpus, when the originals retire, and how fast the whole cycle turns. This block sets those rates, and the loop then runs at that pace. The loop is logged continuously in a working journal, and its images are measured against the archive for distance and spread at regular intervals.

Activity 2. Material sourcing and assembly

From 2027-01-01 to 2027-01-31. Place: Montréal, Québec.

I source and assemble one window prototype, 64 by 48 cm. As a starting set, it takes three interchangeable LED surfaces from a single outdoor module series, at 5, 8 and 10 mm pixel pitch, six modules each, behind acrylic diffusers in several grades, so pitch, frost and brightness can each change while the rest of the prototype stays fixed. Model training continues alongside. By the end of January, the prototype powers on and is ready for testing, then is dismantled and packed for Finland.

Activity 3. Arteles residency

From 2027-02-01 to 2027-02-28. Place: Haukijärvi, Finland.

A month at the Arteles Creative Center in Haukijärvi, on the Silence Awareness Existence program. Exploration days are for experimenting with the window prototype: pitch, frost, brightness and the gap between LED and acrylic. Quiet mornings and silent days are for observing the prototype, adjusting the image model’s parameters and documenting what I see. In non-silent slots, I invite artists in the cohort to an experimentation workshop to experience the research in progress.

Activity 4. Continued explorations and experimentation workshop

From 2027-03-01 to 2027-03-15. Place: Montréal, Québec.

I extend any combinations the residency left open, narrowing the exploration toward its results, while the collapse loop continues. I run an experimentation workshop in my studio with members of the Post Image and Indigenous Futures clusters at the Milieux Institute: a cold read, then the context, then their notes on the prototype and what the work asserts about Indigenous land. Their feedback helps determine what I prototype in Newfoundland.

Activity 5. Experimentation workshops in Newfoundland

From 2027-03-16 to 2027-03-31. Place: Springdale, Newfoundland and Labrador.

I travel with the prototype to Springdale, Newfoundland, and stay with family. My grandmother Doris, Uncle Bob, Aunt Daisy and Aunt Mary, who lived on Pinchard’s Island, sit with the prototype: what they recognize, what is missing, what is failing. Two weeks allow for the workshops to happen at their pace. I document the findings with their consent.

Activity 6. Synthesis and open-source release

From 2027-04-01 to 2027-04-15. Place: Montréal, Québec.

I compile the working journal, the measures recorded through the loop, and the notes and transcripts from all three workshops, and make dark-studio photographs of the window prototype. I write up what held and what did not, and the specifications a final work would have to meet. I publish the training and collapse-loop code under an open-source licence, along with a record of what the model lost.

## Budget

Revenues

| Item | Amount |
|---|---|
| Conseil des arts et des lettres du Québec, amount requested | $25,000 |
| Personal contribution of anything above $25,000, confirmed | $1,402 |
| Total | $26,402 |

Expenses

| Item | Amount |
|---|---|
| Candidate's remuneration, full-time 30 h/wk x $40, $1,200 x 6 weeks | $7,200 |
| Candidate's remuneration, part-time 15 h/wk x $40, $600 x 13 weeks | $7,800 |
| Equipment purchase. Prototype microcomputer; cheaper to buy than rent. | $350 |
| Purchase of materials and/or supplies. 18 LED modules, spares, power, diffusers, mounts, case | $1,800 |
| Research expenses. Cloud GPU for training $400; cloud storage 2 TB $100 | $500 |
| Expert's fees. 5 people x 3 experimentation workshops x $40/hour | $600 |
| Studio rental. Montréal studio $500/mo x 50% x 3 mo; February not claimed | $750 |
| Other realization expenses. Arteles residency fee EUR 1,830 x 1.6063 + 5% FX variance | $3,087 |
| Air travel, 1 person. Montréal-Helsinki return + 5% margin | $1,800 |
| Air travel, 1 person. Montréal-Newfoundland return + 5% margin | $700 |
| Ground transportation, 1 person. YUL taxis $160; Finland transfers $85; Newfoundland fuel $50 | $295 |
| Meals / lodging, $50 x 28 days x 1 person. Residency meals 28 days x EUR 30 + 5% FX variance | $1,400 |
| Travel-related expenses. Travel medical insurance, 30 days in Finland | $120 |
| Total | $26,402 |
