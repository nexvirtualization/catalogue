// SPDX-License-Identifier: AGPL-3.0-only
// Run through validate.py --core so Go's internal-package rules use the selected Core tree.
package main

import (
	"fmt"
	"nex.local/nex/internal/apps"
	"nex.local/nex/internal/protocol"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	paths, err := filepath.Glob(filepath.Join(os.Args[1], "apps", "*", "nex.yaml"))
	must(err)
	for _, path := range paths {
		data, err := os.ReadFile(path)
		must(err)
		p, err := apps.Parse(string(data))
		must(err)
		must(p.ValidateCatalogue())
		s := protocol.AppSettings{Copies: 1, HostIDs: []string{"lab-host"}, Answers: map[string]string{}}
		for _, f := range p.Fields {
			if f.Kind == protocol.AppFieldStorage {
				s.Storage = append(s.Storage, protocol.AppStorage{Variable: f.Variable, Target: "host"})
			} else {
				s.Answers[f.Variable] = f.Default
			}
		}
		facts := apps.ClusterFacts{Hosts: []protocol.AppFormHost{{ID: "lab-host", Enabled: true}}, StorageTargets: []protocol.AppStorageTarget{{ID: "host"}}}
		if problems := apps.Check(p, s, facts); len(problems) > 0 {
			panic(fmt.Sprintf("%s: %v", path, problems))
		}
		rendered, err := apps.Render(apps.RenderInput{Compose: string(data), AppID: "00000000-0000-4000-8000-000000000001", Settings: s, Hosts: s.HostIDs})
		must(err)
		if strings.Contains(rendered, "${") {
			panic("unresolved fields: " + path)
		}
		s.Copies = 2
		if _, err = apps.Render(apps.RenderInput{Compose: string(data), AppID: "00000000-0000-4000-8000-000000000001", Settings: s, Hosts: s.HostIDs}); err == nil {
			panic("multiple writers accepted: " + path)
		}
		s.Copies = 1
		s.Storage = nil
		if _, err = apps.Render(apps.RenderInput{Compose: string(data), AppID: "00000000-0000-4000-8000-000000000001", Settings: s, Hosts: s.HostIDs}); err == nil {
			panic("missing storage accepted: " + path)
		}
		fmt.Println(filepath.Base(filepath.Dir(path)) + ": Core parse, catalogue, settings, render and failure checks passed")
	}
}
func must(err error) {
	if err != nil {
		panic(err)
	}
}
