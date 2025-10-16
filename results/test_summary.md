# Exploit Report – Assertion-Based Trigger in test Binary

## Executive Summary
An input handling flaw was identified in the native "test" binary where a specially crafted input causes an assertion failure. By inserting the key/value pair "fnord:1337", the program reaches an assertion that intentionally fails, marking a solved "challenge". This report documents the technical discovery, analysis, and final working exploit payload.

## Technical Deep-Dive
The vulnerability resides in the function "test_case" (lines 19–44), which parses a string into key/value pairs using a colon (":") delimiter. The key steps are:
- The input is split and stored in an unordered_map.
- A specific check is performed for the key "fnord" (line 39).
- If found, the assertion `SE_TARGET_STATE((it->second == "1337"))` is triggered by a successful match (line 42).  
  Internally, the macro likely uses an assertion (or equivalent) that causes the program to crash when its condition is met.

The design is not vulnerable to classic exploits (e.g., buffer overflow) but is intentionally structured for challenge purposes by asserting on a specific “solved” state.

## Exploitation Methodology
1. **Input Analysis:**  
   - The main function reads input either from a file or STDIN and passes it to "test_case".  
   - Input is tokenized using std::getline and stored in a safe STL unordered_map.

2. **Vulnerability Discovery:**  
   - Code review pinpointed the assertion in "test_case" when the key "fnord" exists.  
   - A controlled test was conducted by piping input "fnord:1337" to the binary.

3. **Bypassing Protections:**  
   - As the code leverages STL functions for input, no memory safety protections (e.g., ASLR, DEP) were required to be bypassed.
   - The exploitation solely depended on satisfying the conditional logic within the map lookup.

4. **Exploit Payload Development:**  
   - The working payload is a simple text string that provides the key "fnord" with the value "1337".
   - Executing the binary with this payload triggers the assertion, indicating a successful state change per the challenge's design.

## Final Working Payload and Demonstration

**Exploit Command:**
  
  echo "fnord:1337" | ./test

**Expected Output:**
  
  test: test.cpp:42: void test_case(std::string): Assertion `!(it->second == "1337")' failed.

This output confirms that the assertion was reached and triggered, successfully demonstrating the intended exploit behavior.

  
*End of Report*