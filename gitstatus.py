#!/usr/bin/env python
from __future__ import print_function

# change this symbol to whatever you prefer
prehash = ':'

from subprocess import Popen, PIPE

gitbinary='/home/lnara002/software/git/git/postinstall/bin/git'

import sys
import os
gitsym = Popen([gitbinary, 'symbolic-ref', 'HEAD'], stdout=PIPE, stderr=PIPE)
branch, error = gitsym.communicate()

error_string = error.decode('utf-8')

if 'fatal: Not a git repository' in error_string:
	sys.exit(0)

branch = branch.decode("utf-8").strip()[11:]

res, err = Popen([gitbinary,'diff','--name-status'], stdout=PIPE, stderr=PIPE).communicate()
err_string = err.decode('utf-8')
if 'fatal' in err_string:
	sys.exit(0)
changed_files = [namestat[0] for namestat in res.decode("utf-8").splitlines()]
staged_files = [namestat[0] for namestat in Popen([gitbinary,'diff', '--staged','--name-status'], stdout=PIPE).communicate()[0].splitlines()]
nb_changed = len(changed_files) - changed_files.count('U')
nb_U = staged_files.count('U')
nb_staged = len(staged_files) - nb_U
staged = str(nb_staged)
conflicts = str(nb_U)
changed = str(nb_changed)
nb_untracked = len([0 for status in Popen([gitbinary,'status','--porcelain',],stdout=PIPE).communicate()[0].decode("utf-8").splitlines() if status.startswith('??')])
untracked = str(nb_untracked)

ahead, behind = 0,0

if not branch: # not on any branch
	branch = prehash + Popen([gitbinary,'rev-parse','--short','HEAD'], stdout=PIPE).communicate()[0].decode("utf-8")[:-1]
else:
	remote_name = Popen([gitbinary,'config','branch.%s.remote' % branch], stdout=PIPE).communicate()[0].decode("utf-8").strip()
	if remote_name:
		merge_name = Popen([gitbinary,'config','branch.%s.merge' % branch], stdout=PIPE).communicate()[0].decode("utf-8").strip()
		if remote_name == '.': # local
			remote_ref = merge_name
		else:
			remote_ref = 'refs/remotes/%s/%s' % (remote_name, merge_name[11:])
		revgit = Popen([gitbinary, 'rev-list', '--left-right', '%s...HEAD' % remote_ref],stdout=PIPE, stderr=PIPE)
		revlist = revgit.communicate()[0]
		if revgit.poll(): # fallback to local
			revlist = Popen([gitbinary, 'rev-list', '--left-right', '%s...HEAD' % merge_name],stdout=PIPE, stderr=PIPE).communicate()[0]
		behead = revlist.decode("utf-8").splitlines()
		ahead = len([x for x in behead if x[0]=='>'])
		behind = len(behead) - ahead

def get_value_from_file(filename):
	try:
		with open(filename,'r') as f:
			value=f.read().strip()
	except:
		value=0
	return value

merge_activity=""
step=0
total=0
gitdir = Popen([gitbinary,'rev-parse','--git-dir'], stdout=PIPE).communicate()[0].decode("utf-8")[:-1]
if os.path.isdir(gitdir+'/rebase-merge'):
	step = get_value_from_file(gitdir+'/rebase-merge/msgnum')
	total = get_value_from_file(gitdir+'/rebase-merge/end')
	if os.path.exists(gitdir+'/rebase-merge/interactive'):
		merge_activity="|REBASE-i"
	else:
		merge_activity="|REBASE-m"
else:
	if os.path.isdir(gitdir+'/rebase-apply'):
		step = get_value_from_file(gitdir+'/rebase-apply/next')
		total = get_value_from_file(gitdir+'/rebase-apply/last')
		if os.path.exists(gitdir+'/rebase-apply/rebasing'):
			merge_activity="|REBASE"
		elif os.path.exists(gitdir+'/rebase-apply/applying'):
			merge_activity="|AM"
		else:
			merge_activity="|AM/REBASE"
	elif os.path.exists(gitdir+'/MERGE_HEAD'):
		merge_activity="|MERGING"
	elif os.path.exists(gitdir+'/CHERRY_PICK_HEAD'):
		merge_activity="|CHERRY-PICKING"
	elif os.path.exists(gitdir+'/REVERT_HEAD'):
		merge_activity="|REVERTING"
	elif os.path.exists(gitdir+'/BISECT_LOG'):
		merge_activity="|BISECTING"

if step != 0 and total != 0:
	merge_activity="%s-(%d/%d)"%(merge_activity,step,total)

out = ' '.join([
	branch,
	str(ahead),
	str(behind),
	staged,
	conflicts,
	changed,
	untracked,
	merge_activity,
	])
print(out, end='')

