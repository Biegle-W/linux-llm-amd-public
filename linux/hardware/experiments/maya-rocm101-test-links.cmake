# Test-only link repair for Maya3384b5e with ROCm10.1/Clang24.
# Pass as CMAKE_PROJECT_INCLUDE in an isolated build; no engine target is changed.
if(CMAKE_CURRENT_SOURCE_DIR STREQUAL CMAKE_SOURCE_DIR)
 function(complete_test_links)
  get_property(all_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
  foreach(test IN LISTS all_targets)
   get_target_property(kind ${test} TYPE)
   if(kind STREQUAL "EXECUTABLE" AND test MATCHES "(test|parity|^hip_)")
    target_link_libraries(${test} PRIVATE strata_prefill roc::hipblaslt)
   endif()
  endforeach()
 endfunction()
 cmake_language(DEFER CALL complete_test_links)
endif()
