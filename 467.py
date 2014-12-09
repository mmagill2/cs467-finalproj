import random
import subprocess
import json
from flask import Flask
import string
from flask import request
from flask import Response
import git

app = Flask(__name__)

def exec_with_stdout(input_list, workingDir='.'):
  try:
    process = subprocess.Popen(input_list, stdout=subprocess.PIPE, cwd=workingDir)
    out, err = process.communicate()
    return out
  except Exception as e:
    return "Error: " + e


def cloc(path):
  try:
    process = subprocess.Popen(['cloc', path, '--csv', '--by-file'], stdout=subprocess.PIPE)
    out, err = process.communicate()
    splitted = out.split("\n\n")
    if len(splitted) != 2:
      return "Error: 'cloc' output sanity check failed"
    return splitted[1]
  except Exception as e:
    return "Error: " + e


def get_random_string(length):
  return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))


def checkout(url):
  name = get_random_string(6)
  try:
    git.Git().clone(url, "repos/" + name)
    totals = exec_with_stdout(['git', 'shortlog', '--numbered', '--summary'], "repos/" + name)
    commits = exec_with_stdout(['git', 'log', '--shortstat'], "repos/" + name)
    direct = "repos/" + name
    return direct, totals, commits
  except Exception as e:
    return "An error occured: " + name, "ERROR", "ERROR"


def make_response(message):
  response = Response(message)
  response.headers.add("Access-Control-Allow-Origin", "*")
  return response
  

@app.route("/run")
def get_repo_json():
  repo_url = request.args.get("url")
  if repo_url is None or len(repo_url) == 0:
    return make_response("An unknown error occured")

  # If we received a valid URL, we go forward to checkout
  checkout_dir, totals, commits = checkout(repo_url)
  if checkout_dir is None:
    return make_response("An unknown error occured while checking out the Git repo")
  if "An error occured" in checkout_dir:
    return make_response("ERROR: " + checkout_dir)

  # If checkout succeeds, we have the path in checkout_dir
  # Now it is time to use 'cloc'
  cloc_result = cloc(checkout_dir)

  combined_results = dict()
  combined_results['cloc_output'] = cloc_result
  combined_results["commit_history"] = commits
  combined_results["loc_contribution"] = totals
  return make_response(json.dumps(combined_results))
  

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=120, debug=True)
