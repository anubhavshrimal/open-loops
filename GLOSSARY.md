# Open Loops

An Orchestrator takes well-defined Tasks from a Tracker, gives each to a Worker that runs in its own Closed Loop until done, and moves the result through review and feedback until the Task is Done.

## Core

**Owner**:
The human who defines Tasks, answers Workers and reviews results.
_Avoid_: user, operator

**Task**:
One unit of work in the Tracker. It points to exactly one Spec.
_Avoid_: ticket, issue, card, item

**Spec**:
The self-contained document that tells a Worker what to do for one Task. It has one of two kinds.
_Avoid_: task description, ticket body

**Build Spec**:
A Spec for a known deliverable, with acceptance criteria.
_Avoid_: task spec, implementation spec

**Exploration Spec**:
A Spec for an open question, with a hypothesis, a success metric and a time budget.
_Avoid_: research plan, experiment doc

**Orchestrator**:
The scheduled agent that moves Tasks between states and spawns Workers. It never does Task work itself.
_Avoid_: scheduler, manager, controller

**Cycle**:
One pass of the Orchestrator over the Tracker.
_Avoid_: tick, run, iteration

**Worker**:
One coding-agent instance assigned to one Task.
_Avoid_: sub-agent, session, executor

**Exploration Worker**:
The Worker for an Exploration Spec: the auto-researcher agent, which runs experiments against one metric.
_Avoid_: research agent, experimenter

**Workspace**:
The isolated directory where a Worker operates.
_Avoid_: sandbox, checkout

**Spawn**:
The start of a Worker on a Task.
_Avoid_: launch, dispatch

**Respawn**:
A new Worker on a Task that had one before, in the same Workspace, continuing the prior work.
_Avoid_: retry, restart, resume

**Closed Loop**:
A Worker's own loop: it works without a human until it meets its Spec's goal or gives up.
_Avoid_: inner loop, agent loop

**Open Loop**:
The outer loop of one Task: Ready, Working, In Review, feedback, Respawn, until Done. It is open because the Owner and reviewers feed new input into it.
_Avoid_: pipeline, workflow

**Follow-up**:
A new instruction from the Owner on a Task that already has results, marked with an agreed prefix.
_Avoid_: action comment, continuation

## States

**Backlog**:
A Task whose definition and Spec the Owner is still shaping, with or without an agent. The Orchestrator ignores it.
_Avoid_: Draft, Unassigned, Icebox

**Ready**:
A Task that is well defined enough for a Worker to take without a human.
_Avoid_: Ready for Agent, To Do, queued

**Working**:
A Task that has a live Worker.
_Avoid_: In Progress, Agent Working

**Blocked**:
A Task whose Worker stopped on a problem that only the Owner can clear.
_Avoid_: Agent Blocked, stuck, failed

**In Review**:
A Task whose result waits for the Owner or a reviewer.
_Avoid_: Awaiting Review, Agent Awaiting Review

**Done**:
A Task that needs nothing more from anyone.
_Avoid_: Agent Done, Closed, Complete

**Gated**:
A Ready Task that waits because an upstream Task is not Done.
_Avoid_: blocked, waiting

**Input Request**:
A live Worker paused on a permission or question prompt.
_Avoid_: blocked, pending prompt

## Review

**PR**:
The reviewable code change a Worker opens. Covers GitHub pull requests, GitLab merge requests and similar.
_Avoid_: CR, MR, change request

**Review comment**:
A comment on a PR from anyone, including the Owner.
_Avoid_: feedback, CR comment

**Review round**:
The work of one Respawn on Review comments or a failed Check: the fix, its publish, and a reply to each Review comment. `review.md` says whether a round adds new commits or amends the commit.
_Avoid_: revision cycle, iteration

**Check**:
An automated pass/fail result on a PR's latest revision, such as a build or test run.
_Avoid_: pipeline status, build status

## Adapters

**Adapter**:
The Owner's own tools for one Slot, plus the notes file that tells the Orchestrator how to use them.
_Avoid_: integration, connector, plugin

**Slot**:
One of the five places where setups differ: Tracker, Host, Runtime, Notifier, Review System.
_Avoid_: adapter kind, extension point

**Contract**:
The plain-language list of capabilities a Slot must supply.
_Avoid_: interface, API, operation set

**Tracker**:
The Slot that stores Tasks and their states.
_Avoid_: board, task manager, project

**Host**:
The Slot that starts the Orchestrator on a schedule.
_Avoid_: scheduler, cron

**Runtime**:
The Slot that spawns, watches and stops Workers.
_Avoid_: worker host, multiplexer

**Notifier**:
The Slot that delivers messages to the Owner.
_Avoid_: channel, alerter

**Review System**:
The Slot that holds PRs, Review comments and Checks.
_Avoid_: code review tool, CR system

## Modules

**Idea Forge**:
The path from a raw idea to a Done Task: capture and refine (the optional modules), then track (the Tracker) and execute (Open Loops).
_Avoid_: idea pipeline, idea funnel
