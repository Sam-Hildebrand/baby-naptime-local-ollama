# Exploitation Report – "fnord:1337" Assertion Trigger

---

## Executive Summary

This report details the analysis and exploitation of a challenge binary ("test2") which processes key-value pairs. The vulnerability resides in the verification logic within the function test_case: when the key "fnord" is provided with the value "1337", an assertion (via SE_TARGET_STATE) is triggered causing the program to abort. Although not a traditional memory corruption vulnerability, it represents a logic flaw that can be exploited to trigger a defined failure state used in challenge scenarios.

---

## Technical Deep-Dive

The binary reads input either from a file or standard input and passes its contents as a C-style string to test_case. Inside test_case, the input is tokenized line-by-line using std::getline, splitting on the colon character. Each valid line (non-empty key and value) is stored in a std::unordered_map. Special macros (SE_STEP and SE_TARGET_STATE) serve as checkpoints during input processing. When the key "fnord" exists in the map and its value is exactly "1337", the macro SE_TARGET_STATE evaluates that condition and triggers an assertion failure. The disassembly reveals conventional stack and argument setup with no memory corruption; the “vulnerability” is an intentional state-check for challenge validation.

---

## Exploitation Methodology

1. **Discovery & Analysis**  
   - Source code review revealed that test_case expects key-value pairs.  
   - The assert at line 42 (in SE_TARGET_STATE) is activated when:
     
     Key: "fnord"  
     Value: "1337"
     
2. **Memory Layout & Protections**  
   - The binary does not exhibit typical memory corruption issues (e.g., buffer overflow), and standard protections (NX, ASLR) are in place.  
   - The exploit bypasses these as it relies solely on controlled input triggering program logic, not memory corruption.

3. **Exploit Development**  
   - Construct an input file containing the line:
     
     fnord:1337  
     
   - This input passes the non-empty key/value checks, stores the mapping, and later causes the check at SE_TARGET_STATE to fail.
  
4. **Proof of Exploitation**  
   - Executing the binary with the crafted input triggers the assertion, confirming our controlled state.

---

## Final Exploit Payload & Execution

Create an input file with the trigger string:

--------------------------------------------------
Command:
--------------------------------------------------
echo "fnord:1337" > input.txt
./test2 input.txt
--------------------------------------------------

Expected Output:
--------------------------------------------------
test2: test2.cpp:42: void test_case(std::string): Assertion `!(it->second == "1337")' failed.
--------------------------------------------------

This output verifies that the payload successfully reached the vulnerable assertion, thus confirming the intended exploit.

---

This concise exploitation report demonstrates how controlled input led to a target state in the binary, confirming both the intended logic flaw and the successful application of the exploit methodology.