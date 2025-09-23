# LeadVille Bridge & Device Architecture Requirements

*Please edit this document to define the technical architecture and use cases*

## 🎯 Bridge Scope & Assignment

### Question 1: Bridge-to-Stage Relationship
**Is each Bridge (Raspberry Pi) responsible for one stage at a time, or can it manage multiple stages simultaneously?**

*Your Answer:* 
A Bridge at this time will only manage 1 stage at a time.  We could look to solve some signal and load issues, and consider multiple stages in the next phase.  There is a logn range idea a bridge could serve as a keystone for a match, communciating with multiple bridges.


### Question 2: Stage Assignment Type
**When you say "Bridge will be Assigned to one Stage" - is this a:**
- [ ] **Runtime assignment** (operator selects which stage this Bridge is managing for a match)
- [ ] **Physical installation** (this Bridge is permanently installed at Stage 3, for example)  
- [ ] **Configuration setting** (this Bridge is configured to only handle Stage X)
- [ ] **Other** (describe below)

*Your Answer:*
yes, a operator will select which stage this Bridge is managing for a match. Each bridge could be redeploy in same or different match at a different stage.


## ⏱️ Timer Device Role

### Question 3: Timer Device Scope
**You mentioned "a Timer" - is this:**
- [ ] **One timer per Bridge** (shared across all targets on that stage)
- [ ] **One timer per stage** (regardless of how many Bridges)
- [ ] **One timer per match** (starts/stops the entire course of fire)
- [ ] **One timer per target** (each target has its own timer)
- [ ] **Other** (describe below)

*Your Answer:*
Each bridge will have just one timer connected at a time.  In a match of multiple stages, each stage will have a bridge with 1 timer assigned.  The Timer will serve with all targets also assigned to that bridge for a stage.  The Timer will control only the start and stop of that particular stage for a bridge.


### Question 4: Timer Function
**What does the Timer device actually control/measure?**

*Your Answer:*
The Timer is a trigger to begin a String of shots.  Once started, the timer also records when each shot was made and records that into other systems like the bridge via BLE.  The timer can also signal the end or when the bridge can stop waiting for more data from the timer.


## 🎯 Impact Sensor Distribution

### Question 5: Sensor-to-Target Assignment
**When Impact Sensors are "assigned to the Stage and targets":**
- [ ] Each **target gets exactly one sensor**
- [ ] Each **target can have multiple sensors**
- [ ] **Some targets have sensors, others don't**
- [ ] **Sensors are shared between targets**
- [ ] **Other** (describe below)

*Your Answer:*
Each target gets 1 sensor.  All steel targets will get one sensor.


### Question 6: Sensor Physical Placement
**Are sensors:**
- [ ] **Physically attached** to targets (mounted on the target)
- [ ] **Positioned nearby** targets (on stands, posts, etc.)
- [ ] **Embedded in target bases/stands**
- [ ] **Other** (describe below)

*Your Answer:*
The mounting and placement of the sensor on the target solution will come down to testing.  Directly on the back of the plate may have excessive force that may damage the devices.  One note, Not all targets are the same, so some calibration of the threashold to indicate an impact and attempt to qualify the type of impact like weather it was a 22lr or 9mm round or maybe less than direct impact like an edge hit could will also need to be done in testing.


### Question 7: Sensor Reassignment
**Can sensors be reassigned between targets:**
- [ ] **During a match** (between shooters)
- [ ] **Between matches only** (when setting up new stage)
- [ ] **Never** (fixed assignment once set)
- [ ] **Dynamically** (based on competition needs)
- [ ] **Other** (describe below)

*Your Answer:*
Sensors can be reassiged between targets for a variaty of reasons during match.  Maybe a sensor goes bad, or the battery goes dead.  The quickest solution would be to replace the sensor, update the target assignement in the bridge for that stage,


## 🌐 Multi-Bridge Scenarios

### Question 8: Bridge Distribution
**In a competition with multiple stages running simultaneously:**
- [ ] Each stage has its **own dedicated Bridge**
- [ ] **Multiple stages share Bridges** (describe how many stages per Bridge)
- [ ] **One master Bridge** controls everything
- [ ] **Bridges are pooled** and assigned as needed
- [ ] **Other** (describe below)

*Your Answer:*
Each stage has its own dedicated Bridge.  There could be a master bridge for the match, know as a keystone in the future.  A Bridge may be reassigned in a match to another stage if needed.


### Question 9: Bridge Coordination
**How do multiple Bridges coordinate (if at all):**
- [ ] **No coordination** (completely independent)
- [ ] **Share match timing** (synchronized start/stop)
- [ ] **Share results/scoring data**
- [ ] **Master/slave relationship**
- [ ] **Peer-to-peer communication**
- [ ] **Central server coordination**
- [ ] **Other** (describe below)

*Your Answer:*
In this phase, there will not be any corrdination, but that does not mean we should not plan for the future.  Each Bridge should have an ID.  Should also have a name that could be changed.  One item to not make this too complex, in very large matches there could be 3 of the exact same stage setup each with their own bridge, timer, targets, impact sensors and etc.  They duplicate stages in a match could be ID'd by color, by a name or a simple A, B or C for example.


## 🔗 Ownership & Connection Logic

### Question 10: Exclusive Sensor Connection
**Should sensors connect exclusively to the Bridge managing their assigned stage:**
- [ ] **Yes** - sensors only connect to their assigned Bridge
- [ ] **No** - sensors can connect to any Bridge in range
- [ ] **Conditional** (describe conditions below)

*Your Answer:*
Sensors only connect to their assigned Bridge.


### Question 11: Multi-Bridge Range Conflicts
**What happens if a sensor is in range of multiple Bridges:**
- [ ] **First Bridge wins** (first to discover gets ownership)
- [ ] **Assigned Bridge wins** (only assigned Bridge can connect)
- [ ] **Strongest signal wins** (best RSSI gets connection)
- [ ] **Manual resolution** (operator chooses)
- [ ] **Error condition** (flag for resolution)
- [ ] **Other** (describe below)

*Your Answer:*
Assigned Bridge wins.  Ideally once a sensor is assigned it is not advertising to other devices.


### Question 12: Ownership Transfer
**How should sensor ownership transfers work when reassigning stages:**
- [ ] **Automatic** (sensor reconnects to new Bridge immediately)
- [ ] **Manual disconnect/reconnect** (operator initiated)
- [ ] **Graceful handoff** (old Bridge releases, new Bridge acquires)
- [ ] **Restart required** (sensor must be power cycled)
- [ ] **Other** (describe below)

*Your Answer:*
I know BLE can have some hassel over who owns a device and how it can be released and reassigned.  Ideally this is done as easy as possible with out too many downsides.


## 🏃‍♂️ Match Workflow

### Question 13: Discovery & Assignment Trigger
**In a typical match sequence, who/what triggers sensor discovery and assignment:**
- [ ] **Range Officer** (manual trigger before each stage)
- [ ] **Automatic** (when Bridge starts up)
- [ ] **Match Director** (central control)
- [ ] **Scheduler** (time-based or event-based)
- [ ] **Shooter** (when checking in to stage)
- [ ] **Other** (describe below)

*Your Answer:*
Ideally the Match Director, or their deligate will preconfigure the sensors to a bridge and define the target each should be assigned to with a label.  Match day setup can be a bit of a rodeo, so as much that we can do ahead the better.


### Question 14: Assignment Timing
**Are assignments made:**
- [ ] **Once per stage setup** (stays fixed for entire stage)
- [ ] **Before each shooter** (can change between shooters)
- [ ] **Before each string/course** (multiple courses per shooter)
- [ ] **Dynamically during shooting** (real-time reassignment)
- [ ] **Other** (describe below)

*Your Answer:*
The Sensor and Timer assignments should be done once for match unless maintenance is required.


### Question 15: Stage-to-Match Relationship
**What's the relationship between stage assignment and match timing:**
- [ ] **Stage assignment is independent** of match timing
- [ ] **Stage assignment triggers** match timer
- [ ] **Match timer controls** stage assignment
- [ ] **They are synchronized** but independent
- [ ] **Other** (describe below)

*Your Answer:*
This is a tricky question an may not be the answer needed.  There is not match timing in my view.  Each Match there are 1 or more stages, usually 4, but could be 6 or 8.  So in a match, on a stage, an RO will use the timer to trigger the start beep, record the shots, as the target sensors detect impacts.  There can be 1 to 30 or more shots take place until the athlete is done and the RO trigger the end of the string on the timer.  The timer could also idle out after 5minutes or so of no shots being detected.  The end of the previous string could also be signalled by the timer starting again.  Not all strings will be scored, sme may be a reshoot so when we get to the scoring side of the project we will need to iron that out.  And all of the start, shots, imapcts and stops is recorded to the bridge.


## 📝 Additional Technical Details

### Question 16: Competition Types
**What types of competitions will this system support:**

*Your Answer:*
The 2 main types at this time are SASP and Steel Challenge matches.  However new uses cases for team practice and other leagues when the sensors and bridge will assist the shooting game may be a possibility.


### Question 17: Scalability Requirements
**What are the expected scale requirements:**
- Number of simultaneous stages: ___
- Number of sensors per stage: ___
- Number of Bridges in a match: ___
- Number of concurrent shooters: ___

*Your Answer:*
The could be 1 to 24 or more stages going on in parallel.  The current games of SASP and Steel Challege typucally have 5 or 6 target plates.


### Question 18: Performance Requirements
**What are the critical performance requirements:**

*Your Answer:*
The system need to be trusted and reliable.  With fair to decent performance.


### Question 19: Failure Scenarios
**How should the system handle failures:**

*Your Answer:*
The risk assessment aspects of this have not be worked on, but the main one is fast recovery of equipment and preseervation of data with integrity are important.


### Question 20: Integration Requirements
**Does this system need to integrate with other systems:**

*Your Answer:*
At this time, there is no need for compatibilitiy, but the future, the data will be valuable and preserved for key insights, reporting and awards.


---

## 🎯 Summary Section
*After answering the questions above, please provide a high-level summary of the intended architecture:*

### System Architecture Summary
The current phase is focused on 1 bridge assigned to a stage, with one discovered timer and 5-6 impact sensors that are defined to targets in a stage configuration.


### Key Technical Requirements
TBD, essentially a tracking tool used report secondary validation of impact with data, while paint be distribued is a visual confirmation is primary.


### Implementation Priorities
We have a lot of progress, and no one priority stands out besides getting to the MVP for a PoC.


---

## 🔍 Follow-up Questions for Implementation Details

### Question 21: Bridge Identity & Assignment Interface
**You mentioned "Each Bridge should have an ID" and "Should also have a name that could be changed" - should I implement:**
- [ ] A **Bridge configuration screen** where operators can set Bridge name/ID
- [ ] **Stage assignment interface** where operators select which stage this Bridge manages
- [ ] **Both of the above**
- [ ] **Other** (describe below)

*Your Answer:*
Both


### Question 22: Sensor Assignment Process Location
**You said "Match Director will preconfigure sensors to a bridge and define target each should be assigned" - should this be:**
- [ ] **Same Stage Setup interface** we just built (but restricted to assigned Bridge)
- [ ] **New Bridge-specific configuration** separate from the general stage setup
- [ ] **Central management interface** that assigns sensors to multiple Bridges
- [ ] **Other** (describe below)

*Your Answer:*
Same Stage Setup interface is fine, but later we will simplify the user experience.  If you can do this now, that would be fine.


### Question 23: BLE Connection Priority Logic
**For "Assigned Bridge wins" - when a sensor is discovered by multiple Bridges:**
- [ ] **Non-assigned Bridges ignore** the sensor completely during discovery
- [ ] **Discover but refuse to connect** to sensors assigned to other Bridges
- [ ] **Attempt connection but gracefully yield** to assigned Bridge
- [ ] **Other** (describe below)

*Your Answer:*
This is a tricky one to answer as what makes this safe, does not always make it easy.  Find that balance and we may need to explore which is better.


### Question 24: Database Schema for Ownership
**Currently sensors have `target_config_id` (which target they're assigned to). Should I add:**
- [ ] **`bridge_id`** field to sensors table to track which Bridge owns each sensor
- [ ] **Bridge-to-Stage assignment** table to track which Bridge is managing which stage
- [ ] **Both of the above**
- [ ] **Different approach** (describe below)

*Your Answer:*
I imagine both make sense, but I am open to any approach.  I think the right answer would be to have a Keystone that could have a whole match be configured and pushed to the bridge of each stage.  These varaibles will like be used in logs, screens and other locations throughout the solution.  Would also be good to track by Match ID and Match Name.


### Question 25: Bridge Reassignment Workflow
**When a Bridge needs to be reassigned to a different stage:**
- [ ] **Automatic sensor release** (all sensors disconnect and become available)
- [ ] **Manual sensor migration** (operator moves sensors to new Bridge)
- [ ] **Sensor ownership stays with stage** (new Bridge inherits stage's sensors)
- [ ] **Other** (describe below)

*Your Answer:*
I am open minded here as I am not sure of the best solution or what will make most sense to the users.  I did build into the bridge at start up to reconnect with the previously assigned timer and sensors until the Match Director reconfigures them.  I imagined the bridge will be restarted for a few reasons and the persistance is usability feature to not have to reassign bridge stage devices.

---

*Please edit this document with your answers and save it. This will help define the technical architecture for the BLE connection and ownership logic.*