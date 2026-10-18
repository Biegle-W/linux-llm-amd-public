# Desktop launcher icons

Six original SVG launcher symbols: llama (amber), SGLang (green network), vLLM
(violet lightning), Strata (cyan layers), dsh (blue terminal/chat) and Turnstone
(coral bird). These are custom launcher artwork, not official project logos.
They are source vectors with no fonts, external assets, scripts or network reads.

The desktop entry `Icon=` uses an absolute path to the corresponding SVG in
`launchers/icons/`. Keep that directory when copying/reinstalling the setup.
For another install location, update `Icon=` together with the existing `Exec=`
and `Path=` values in the desktop files, then copy them to your Desktop. Preserve
the executable bit and existing desktop trust state. This only changes appearance;
backend commands, terminal behavior, model selection and Strata's RAM gate remain.

Original artwork is provided under the MIT license in [LICENSE](LICENSE).
